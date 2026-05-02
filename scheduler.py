from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import logging
from backend_scraper import get_dashboard_data
from database import (
    save_to_db, get_keywords_list, init_db,
    set_next_run_time, set_last_run_time, get_schedule_hours,
    get_high_citation_threshold,
    # ──────────────────────────────────────────────────────────
    # [수정] save_high_citation_alerts import 추가
    # 
    # 문제 원인:
    #   - 기존 코드에서 save_high_citation_alerts 를 import하지 않아
    #     고인용 논문 알림이 DB에 전혀 저장되지 않는 버그 존재
    # ──────────────────────────────────────────────────────────
    save_high_citation_alerts,
)

init_db()
scheduler = BlockingScheduler()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def job():
    logger.info("🚀 자동 수집 시작")

    # ──────────────────────────────────────────────────────────
    # [이슈1 — 스케줄러 측 확인]
    # 
    # 스케줄러는 job() 실행 시점마다 get_keywords_list()를 DB에서
    # 직접 조회하기 때문에, 설정 탭에서 키워드를 추가/삭제하면
    # 다음 스케줄 실행 때 자동으로 반영됩니다. 별도 수정 불필요.
    #
    # app.py 측 문제(selectbox가 갱신 안 됨)는 app.py에서 수정했습니다.
    # ──────────────────────────────────────────────────────────
    keywords = get_keywords_list()

    if not keywords:
        logger.warning("등록된 키워드가 없습니다.")
        return

    threshold      = get_high_citation_threshold()
    schedule_hours = get_schedule_hours()

    success_count = 0
    for kw in keywords:
        try:
            result      = get_dashboard_data(kw, threshold)
            papers      = result["papers"]
            high_papers = result["high_papers"]

            saved = save_to_db(kw, papers)
            logger.info(f"   - {kw}: {len(papers)}건 수집, {saved}건 신규 저장")

            # ──────────────────────────────────────────────────
            # [수정] 고인용 알림 DB 저장 호출 추가
            #
            # 기존: save_high_citation_alerts() 호출 자체가 누락되어
            #       고인용 알림 테이블이 항상 비어 있었음
            # 변경: 수집 직후 고인용 논문 목록을 DB에 저장
            # ──────────────────────────────────────────────────
            if high_papers:
                save_high_citation_alerts(kw, high_papers)
                logger.info(f"   - 고인용 알림 {len(high_papers)}건 저장")

            success_count += 1
        except Exception as e:
            logger.error(f"   - {kw} 수집 실패: {e}")

    now      = datetime.now()
    next_run = now + timedelta(hours=schedule_hours)
    set_last_run_time(now.strftime("%Y-%m-%d %H:%M:%S"))
    set_next_run_time(next_run.strftime("%Y-%m-%d %H:%M:%S"))

    logger.info(f"✅ 수집 완료 ({success_count}/{len(keywords)} 키워드 성공)")
    logger.info(f"🕐 다음 예정 시각: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")


# ──────────────────────────────────────────────────────────────
# 스케줄 등록 (DB에서 최신 interval 조회)
# ──────────────────────────────────────────────────────────────
schedule_hours = get_schedule_hours()
scheduler.add_job(job, 'interval', hours=schedule_hours, id='paper_collection')

# 시작 시 최초 1회 즉시 실행
try:
    job()
except Exception as e:
    logger.error(f"초기 수집 실패: {e}")

logger.info(f"⏰ i-SENS 대시보드 스케줄러 가동 중... ({schedule_hours}시간마다)")
scheduler.start()