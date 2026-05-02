import urllib.request
import urllib.parse
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
ALERT_LOG_PATH = BASE_DIR / "high_citation_alerts.log"

SEMANTIC_SCHOLAR_DELAY = 3
MAX_RETRIES = 3
REQUEST_TIMEOUT = 20

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def fetch_europe_pmc(keyword, max_results=30):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(keyword)}&format=json&resultType=core&pageSize={max_results}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "i-SENS-Dashboard/2.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        papers = []
        for item in data.get("resultList", {}).get("result", []):
            pmid = item.get("pmid", "")
            
            affiliation = item.get("affiliation", [])
            country = "unknown"
            if isinstance(affiliation, list) and len(affiliation) > 0:
                if isinstance(affiliation[0], dict):
                    country = affiliation[0].get("country", "unknown")
            
            papers.append({
                "source": "Europe PMC",
                "title": item.get("title", "제목 없음"),
                "link": f"https://europepmc.org/article/MED/{pmid}" if pmid else item.get("url", ""),
                "journal": item.get("journalTitle", ""),
                "citation_count": item.get("citedByCount", 0),
                "language": item.get("language", "en"),
                "country": country,
                "is_preprint": 0,
                "journal_quality": "SCI" if item.get("journalTitle") else "unknown"
            })
        return papers
    except Exception as e:
        logger.error(f"Europe PMC 수집 실패 ({keyword}): {e}")
        return []

def fetch_semantic_scholar(keyword, max_results=30):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(keyword)}&limit={max_results}&fields=title,url,citationCount,venue"
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(SEMANTIC_SCHOLAR_DELAY)
            req = urllib.request.Request(url, headers={"User-Agent": "i-SENS-Dashboard/2.0"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            return [{
                "source": "Semantic Scholar",
                "title": i.get("title", ""),
                "link": i.get("url", ""),
                "journal": i.get("venue", ""),
                "citation_count": i.get("citationCount", 0),
                "language": "en",
                "country": "unknown",
                "is_preprint": 0,
                "journal_quality": "Scopus" if i.get("venue") else "unknown"
            } for i in data.get("data", [])]
        except Exception as e:
            logger.warning(f"Semantic Scholar 재시도 {attempt+1}/{MAX_RETRIES}: {e}")
            time.sleep(5)
    logger.error(f"Semantic Scholar 최종 실패: {keyword}")
    return []

def fetch_openalex(keyword, max_results=30):
    url = f"https://api.openalex.org/works?search={urllib.parse.quote(keyword)}&per-page={max_results}&sort=relevance_score:desc"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "i-SENS-Dashboard/2.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        papers = []
        for item in data.get("results", []):
            is_preprint = 1 if item.get("type") == "preprint" else 0
            language = item.get("language", "en")
            
            journal = ""
            primary = item.get("primary_location")
            if primary and isinstance(primary, dict):
                source = primary.get("source")
                if source and isinstance(source, dict):
                    journal = source.get("display_name", "")
            
            country = "unknown"
            authorships = item.get("authorships", [])
            if authorships and len(authorships) > 0:
                countries = authorships[0].get("countries", [])
                if countries and len(countries) > 0:
                    country = countries[0]
            
            papers.append({
                "source": "OpenAlex",
                "title": item.get("title", "제목 없음"),
                "link": item.get("doi", "") or item.get("id", ""),
                "journal": journal,
                "citation_count": item.get("cited_by_count", 0),
                "language": language,
                "country": country,
                "is_preprint": is_preprint,
                "journal_quality": "SCI" if not is_preprint else "Preprint"
            })
        return papers
    except Exception as e:
        logger.error(f"OpenAlex 수집 실패 ({keyword}): {e}")
        return []

def fetch_crossref(keyword, max_results=30):
    url = f"https://api.crossref.org/works?query={urllib.parse.quote(keyword)}&rows={max_results}&sort=relevance"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "i-SENS-Dashboard/2.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        papers = []
        for item in data.get("message", {}).get("items", []):
            title = item.get("title", ["제목 없음"])[0] if item.get("title") else "제목 없음"
            journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
            doi = item.get("DOI", "")
            link = f"https://doi.org/{doi}" if doi else ""
            language = item.get("language", "en")
            country = item.get("country", "unknown")
            is_preprint = 1 if item.get("type") == "posted-content" else 0
            
            papers.append({
                "source": "Crossref",
                "title": title,
                "link": link,
                "journal": journal,
                "citation_count": 0,
                "language": language,
                "country": country,
                "is_preprint": is_preprint,
                "journal_quality": "SCI" if not is_preprint else "Preprint"
            })
        return papers
    except Exception as e:
        logger.error(f"Crossref 수집 실패 ({keyword}): {e}")
        return []

def get_dashboard_data(keyword, threshold=50):
    """소스별 결과 + 실패 정보 반환"""
    results = {
        "papers": [],
        "high_papers": [],
        "failed_sources": []
    }
    
    # Europe PMC
    try:
        papers_epmc = fetch_europe_pmc(keyword)
        results["papers"].extend(papers_epmc)
    except Exception as e:
        results["failed_sources"].append(("Europe PMC", str(e)))
    
    # Semantic Scholar (429 특별 처리)
    try:
        papers_ss = fetch_semantic_scholar(keyword)
        results["papers"].extend(papers_ss)
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            results["failed_sources"].append(("Semantic Scholar", "조회 제한 (5분에 1회)"))
        else:
            results["failed_sources"].append(("Semantic Scholar", str(e)))
    
    # OpenAlex
    try:
        papers_oa = fetch_openalex(keyword)
        results["papers"].extend(papers_oa)
    except Exception as e:
        results["failed_sources"].append(("OpenAlex", str(e)))
    
    # Crossref
    try:
        papers_cr = fetch_crossref(keyword)
        results["papers"].extend(papers_cr)
    except Exception as e:
        results["failed_sources"].append(("Crossref", str(e)))
    
    # 고인용 필터링
    results["high_papers"] = [p for p in results["papers"] if (p.get('citation_count') or 0) >= threshold]
    
    return results