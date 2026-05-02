import pandas as pd
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
import logging

# Robust path handling
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "papers.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        
        # [수정 버그1] DROP TABLE 제거 → IF NOT EXISTS로 변경
        # 기존: 앱 실행/새로고침마다 테이블이 삭제되어 데이터 전부 소실
        # 변경: 테이블이 없을 때만 생성, 기존 데이터 보존
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT UNIQUE,
                link           TEXT,
                source         TEXT,
                journal        TEXT,
                citation_count INTEGER DEFAULT 0,
                collected_date TEXT,
                language       TEXT DEFAULT 'unknown',
                country        TEXT DEFAULT 'unknown',
                is_preprint    INTEGER DEFAULT 0,
                journal_quality TEXT DEFAULT 'unknown'
            )
        """)
        
        c.execute("CREATE TABLE IF NOT EXISTS keywords (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT UNIQUE)")
        c.execute("CREATE TABLE IF NOT EXISTS article_keywords (article_id INTEGER, keyword_id INTEGER, UNIQUE(article_id, keyword_id))")
        c.execute("CREATE TABLE IF NOT EXISTS collection_log (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT, total_found INTEGER, newly_saved INTEGER, logged_at TEXT)")
        c.execute("""
            CREATE TABLE IF NOT EXISTS high_citation_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                title TEXT,
                citation_count INTEGER,
                link TEXT,
                journal TEXT,
                detected_at TEXT
            )
        """)
        c.execute("CREATE TABLE IF NOT EXISTS app_metadata (key TEXT PRIMARY KEY, value TEXT)")

        c.execute("CREATE INDEX IF NOT EXISTS idx_citation ON articles(citation_count)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_date ON articles(collected_date)")

def _get_setting(key, default=None):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

def _set_setting(key, value):
    with get_conn() as conn:
        conn.cursor().execute("INSERT OR REPLACE INTO app_metadata (key, value) VALUES (?, ?)", (key, str(value)))

def get_high_citation_threshold():
    return int(_get_setting("high_citation_threshold", 50))

def set_high_citation_threshold(val):
    _set_setting("high_citation_threshold", val)

def get_schedule_hours():
    return int(_get_setting("schedule_hours", 24))

def set_schedule_hours(val):
    _set_setting("schedule_hours", val)

def set_next_run_time(next_run_str):
    _set_setting("next_run_time", next_run_str)

def get_next_run_time():
    return _get_setting("next_run_time")

def set_last_run_time(last_run_str):
    _set_setting("last_run_time", last_run_str)

def get_last_run_time():
    return _get_setting("last_run_time")

def save_high_citation_alerts(keyword, high_papers):
    if not high_papers:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        c = conn.cursor()
        for p in high_papers:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO high_citation_alerts 
                    (keyword, title, citation_count, link, journal, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (keyword, p.get('title'), p.get('citation_count'), p.get('link'), p.get('journal'), now))
            except Exception as e:
                logger.warning(f"고인용 알림 저장 실패: {e}")

def save_to_db(keyword, papers):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved_count = 0

    with get_conn() as conn:
        c = conn.cursor()
        
        # 키워드 등록
        c.execute("INSERT OR IGNORE INTO keywords(keyword) VALUES (?)", (keyword,))
        c.execute("SELECT id FROM keywords WHERE keyword=?", (keyword,))
        kw_id = c.fetchone()[0]

        for p in papers:
            try:
                # 단순 INSERT (중복이면 무시)
                # [수정 버그3] language, country, is_preprint, journal_quality 컬럼 추가
                # 기존: 4개 컬럼 누락 → 라이브러리 필터 전부 unknown
                c.execute("""
                    INSERT OR IGNORE INTO articles 
                    (title, link, source, journal, citation_count, collected_date,
                     language, country, is_preprint, journal_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p['title'],
                    p['link'],
                    p['source'],
                    p.get('journal', ''),
                    p.get('citation_count', 0),
                    now,
                    p.get('language', 'unknown'),
                    p.get('country', 'unknown'),
                    p.get('is_preprint', 0),
                    p.get('journal_quality', 'unknown'),
                ))
                
                if c.rowcount > 0:
                    saved_count += 1
                    
            except Exception as e:
                logger.warning(f"저장 실패: {e}")
                continue

        # 로그 기록
        c.execute("""
            INSERT INTO collection_log (keyword, total_found, newly_saved, logged_at) 
            VALUES (?, ?, ?, ?)
        """, (keyword, len(papers), saved_count, now))

    return saved_count

def get_all_data():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM articles ORDER BY id DESC", conn)

def get_keywords_list():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM keywords ORDER BY id ASC")
        return [row[0] for row in cursor.fetchall()]

def add_target_keyword(kw):
    try:
        with get_conn() as conn:
            conn.cursor().execute("INSERT INTO keywords (keyword) VALUES (?)", (kw.strip(),))
        logger.info(f"키워드 추가: {kw}")
        return True
    except Exception as e:
        logger.warning(f"키워드 추가 실패: {e}")
        return False

def delete_target_keyword(kw):
    try:
        with get_conn() as conn:
            conn.cursor().execute("DELETE FROM keywords WHERE keyword = ?", (kw,))
        logger.info(f"키워드 삭제: {kw}")
    except Exception as e:
        logger.error(f"키워드 삭제 실패: {e}")

def reset_all_data():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM articles")
        c.execute("DELETE FROM article_keywords")
        c.execute("DELETE FROM collection_log")
        c.execute("DELETE FROM high_citation_alerts")
        logger.warning("전체 데이터 초기화 완료 (고인용 알림 포함)")

def get_collection_log():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT keyword, total_found, newly_saved, logged_at FROM collection_log ORDER BY id DESC LIMIT 50", conn)

def get_journal_stats():
    with get_conn() as conn:
        return pd.read_sql_query('''
            SELECT journal, COUNT(*) AS paper_count, AVG(citation_count) AS avg_citation, MAX(citation_count) AS max_citation
            FROM articles WHERE journal != '' AND citation_count IS NOT NULL
            GROUP BY journal HAVING COUNT(*) >= 2 ORDER BY avg_citation DESC LIMIT 20
        ''', conn)

def get_high_citation_alerts(limit=30):
    with get_conn() as conn:
        return pd.read_sql_query("""
            SELECT keyword, title, citation_count, link, journal, detected_at 
            FROM high_citation_alerts 
            ORDER BY id DESC LIMIT ?
        """, conn, params=(limit,))