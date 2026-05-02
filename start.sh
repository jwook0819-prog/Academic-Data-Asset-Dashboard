#!/bin/bash
# ============================================================
# i-SENS 대시보드 Railway 시작 스크립트
# - Streamlit 대시보드 (app.py) 와 스케줄러 (scheduler.py) 를
#   동시에 실행합니다.
# ============================================================

echo "🚀 i-SENS 대시보드 시작..."

# 스케줄러를 백그라운드에서 실행
python scheduler.py &
SCHEDULER_PID=$!
echo "⏰ 스케줄러 시작 (PID: $SCHEDULER_PID)"

# Streamlit 대시보드를 포그라운드에서 실행
# Railway는 PORT 환경변수를 자동 주입합니다
streamlit run app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false

# Streamlit이 종료되면 스케줄러도 함께 종료
kill $SCHEDULER_PID