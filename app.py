import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from backend_scraper import get_dashboard_data
from database import (
    init_db, get_all_data, get_keywords_list, add_target_keyword,
    delete_target_keyword, reset_all_data, get_collection_log,
    get_journal_stats, get_high_citation_alerts, get_next_run_time,
    get_last_run_time, set_high_citation_threshold, get_high_citation_threshold,
    set_schedule_hours, get_schedule_hours, save_to_db,
    set_next_run_time, set_last_run_time,
    toggle_star, save_memo, get_starred_articles
)

st.set_page_config(page_title="i-SENS 학술 자료 수집 대시보드", page_icon="🧬", layout="wide")

# ==================== 고급 디자인 CSS (최종) ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --isens-blue:   #171c8f;
        --isens-green:  #78BE20;
        --isens-dark:   #141943;
        --isens-gray:   #53565A;
        --isens-bg:     #f4f6fb;
    }

    html, body, .stApp {
        background-color: var(--isens-bg) !important;
        font-family: 'Inter', system-ui, sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #171c8f 0%, #232aa8 100%);
        padding: 1.2rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.4rem;
        color: white;
    }
    .main-header h1 { font-size: 1.4rem; font-weight: 700; margin: 0 0 0.15rem; }
    .main-header p  { font-size: 0.82rem; margin: 0; opacity: 0.8; }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        border: 1px solid #eaecf4;
        height: 95px !important;
        min-height: 92px;
        display: flex;
        align-items: center;
    }
    .metric-value {
        font-size: 1.95rem;
        font-weight: 700;
        color: var(--isens-blue);
        line-height: 1.1;
        margin: 0;
    }
    .metric-value-sm {
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--isens-blue);
        line-height: 1.2;
        margin: 0;
    }
    .metric-label { 
        font-size: 0.78rem; 
        color: #6c757d; 
        margin-top: 4px; 
    }

    .paper-card {
        background: white;
        border-radius: 10px;
        padding: 0.95rem 1.2rem;
        border-left: 4px solid var(--isens-blue);
        margin-bottom: 0.55rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }
    .paper-card a {
        font-weight: 600;
        color: var(--isens-blue);
        text-decoration: none;
        font-size: 0.9rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.45;
    }
    .paper-card a:hover { text-decoration: underline; }
    .paper-meta { font-size: 0.78rem; color: #6c757d; margin-top: 0.3rem; }
    .badge-citation {
        display: inline-block;
        padding: 0.22rem 0.65rem;
        background: #e6f7d8;
        color: #3d7a0f;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.82rem;
        white-space: nowrap;
        flex-shrink: 0;
    }

    .stButton > button[kind="primary"],
    .stButton > button:not([kind]) {
        background: linear-gradient(90deg, #171c8f, #2334b0) !important;
        color: white !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: var(--isens-blue) !important;
        border: 1.5px solid var(--isens-blue) !important;
        border-radius: 9px !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #f0f2fb !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--isens-dark) !important;
        min-width: 220px !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] caption {
        color: #c8cce8 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] > label:first-child {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #9ca3ff !important;
        margin-bottom: 0.4rem !important;
        padding-left: 0.2rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: column !important;
        gap: 3px !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        font-size: 0.97rem !important;
        font-weight: 500 !important;
        padding: 0.55rem 0.8rem !important;
        border-radius: 8px !important;
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
        color: #c8cce8 !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,0.07) !important;
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) label {
        background: linear-gradient(90deg, #1f2552, #252b5e) !important;
        color: #9fd44a !important;
        font-weight: 700 !important;
        border-left: 5px solid #78BE20 !important;
        padding-left: 0.65rem !important;
        box-shadow: 0 4px 12px rgba(120, 190, 32, 0.2);
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radio"] {
        display: none !important;
    }

    [data-testid="stDataFrame"] table { font-size: 0.875rem !important; }
    [data-testid="stDataFrame"] thead th {
        background: #f0f2fb !important;
        color: var(--isens-blue) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        padding: 0.55rem 0.75rem !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {
        background: #f5f6fd !important;
    }

    hr { border-color: #e5e7f0 !important; }
    [data-testid="stExpander"] summary {
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: var(--isens-blue) !important;
    }
</style>
""", unsafe_allow_html=True)


init_db()

# ==================== 헤더 ====================
df_header = get_all_data()
last_run  = get_last_run_time() or "-"
last_date = last_run[:10] if last_run != "-" else "-"
total_cnt = f"{len(df_header):,}" if not df_header.empty else "0"

st.markdown(f"""
<div class="main-header">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="width:44px;height:44px;background:#78BE20;border-radius:11px;
                  display:flex;align-items:center;justify-content:center;
                  color:white;font-weight:800;font-size:1.4rem;flex-shrink:0;">i</div>
      <div>
        <h1>i-SENS 학술 자료 수집 대시보드</h1>
        <p>Sensing Ahead, Caring More · 실시간 학술 인사이트</p>
      </div>
    </div>
    <div class="header-stat">
      누적 논문<br><b>{total_cnt} 건</b>
      &nbsp;&nbsp;|&nbsp;&nbsp;
      최근 수집<br><b>{last_date}</b>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==================== 사이드바 ====================
with st.sidebar:
    st.markdown(
        "<p style='font-size:0.68rem;font-weight:600;letter-spacing:.1em;"
        "color:#5a6099;text-transform:uppercase;margin:0.6rem 0 0.5rem;padding-left:0.8rem;'>"
        "NAVIGATION</p>",
        unsafe_allow_html=True
    )
    page = st.radio(
        "메뉴",
        ["📊  데이터 수집", "📚  라이브러리", "🆕  신규 수집", "⚙️  설정"],
        label_visibility="collapsed"
    )
    st.divider()

    # ──────────────────────────────────────────────────────────
    # [수정 이슈2] 카운트다운 동작 수정
    #
    # 문제 원인:
    #   - run_every=1 은 정수(int)를 받지 않는 버전이 있음
    #   - Streamlit 1.37 미만에서는 run_every 자체가 silently 무시됨
    #
    # 해결 방법:
    #   - run_every=timedelta(seconds=1) 로 명시적 timedelta 전달
    #   - 혹시 @st.fragment 자체가 지원 안 될 경우를 대비해 try/except 폴백 제거하고
    #     timedelta 방식으로 통일 (가장 안정적인 방법)
    # ──────────────────────────────────────────────────────────
    @st.fragment(run_every=timedelta(seconds=1))
    def sidebar_countdown():
        st.markdown(
            "<p style='font-size:0.68rem;font-weight:600;letter-spacing:.1em;"
            "color:#5a6099;text-transform:uppercase;margin:0 0 0.5rem;padding-left:0.2rem;'>"
            "NEXT AUTO COLLECT</p>",
            unsafe_allow_html=True
        )
        next_run_str = get_next_run_time()
        if next_run_str:
            try:
                next_run      = datetime.strptime(next_run_str, "%Y-%m-%d %H:%M:%S")
                remaining     = (next_run - datetime.now()).total_seconds()
                schedule_hours = get_schedule_hours()
                if remaining > 0:
                    h, rem = divmod(int(remaining), 3600)
                    m, s   = divmod(rem, 60)
                    ratio  = max(0.0, min(1.0, 1.0 - remaining / (schedule_hours * 3600)))
                    st.progress(ratio)
                    st.markdown(
                        f"<div style='text-align:center;font-size:1.6rem;font-weight:700;"
                        f"color:#c5c9ff;letter-spacing:3px;margin:0.3rem 0;'>"
                        f"{h:02d}:{m:02d}:{s:02d}</div>",
                        unsafe_allow_html=True
                    )
                    st.caption(f"예정: {next_run.strftime('%m/%d %H:%M')}")
                else:
                    st.info("🔄 수집 중이거나 곧 시작합니다...")
            except Exception:
                st.caption("시각 정보를 읽을 수 없습니다.")
        else:
            st.caption("scheduler.py를 실행하면\n카운트다운이 시작됩니다.")

    sidebar_countdown()
    st.divider()
    st.caption("v2.3 · i-SENS 교육지원")


# ==================== 페이지: 데이터 수집 ====================
if page == "📊  데이터 수집":
    st.subheader("실시간 데이터 수집")
    st.caption("최신 논문을 빠르게 수집하고 핵심 인사이트를 확인하세요")

    # ──────────────────────────────────────────────────────────
    # [수정 이슈1] 키워드 목록을 매 렌더링마다 DB에서 직접 조회
    # 
    # 문제 원인:
    #   - 설정 탭에서 키워드 추가 후 st.rerun()을 호출하지만,
    #     다른 탭(데이터 수집)으로 전환 시 kws 가 최신 상태인지
    #     보장되지 않는 케이스 존재
    #   - 특히 selectbox 의 options 가 캐시되어 새 키워드가 안 보임
    #
    # 해결 방법:
    #   - get_keywords_list() 를 페이지 진입 시마다 직접 호출 (캐시 없음)
    #   - st.cache_data 를 쓰지 않아 항상 최신 DB 상태 반영
    # ──────────────────────────────────────────────────────────
    kws = get_keywords_list()  # 항상 DB에서 신선하게 조회

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        if kws:
            sel_kw = st.selectbox("키워드 선택", kws, label_visibility="collapsed")
        else:
            sel_kw = st.text_input(
                "키워드 입력",
                placeholder="예: continuous glucose monitoring",
                label_visibility="collapsed"
            )
    with col2:
        collect_btn = st.button("🚀 수집 시작", use_container_width=True)
    with col3:
        bulk_btn = st.button("🔄 일괄 수집", use_container_width=True,
                             type="secondary", disabled=not kws)

    if collect_btn and sel_kw.strip():
        with st.status(f"'{sel_kw}' 수집 중...", expanded=True) as status:
            try:
                threshold   = get_high_citation_threshold()
                data        = get_dashboard_data(sel_kw, threshold)
                papers      = data["papers"]
                high_papers = data["high_papers"]
                for source, reason in data.get("failed_sources", []):
                    st.warning(f"⚠️ {source}: {reason}")
                saved = save_to_db(sel_kw, papers)
                # 수동 수집 완료 시 last/next run time DB 기록 → 사이드바 카운트다운 시작
                now      = datetime.now()
                next_run = now + timedelta(hours=get_schedule_hours())
                set_last_run_time(now.strftime("%Y-%m-%d %H:%M:%S"))
                set_next_run_time(next_run.strftime("%Y-%m-%d %H:%M:%S"))
                status.update(
                    label=f"✅ 완료 · {saved}건 저장 · 고인용 {len(high_papers)}건",
                    state="complete"
                )
                if high_papers:
                    st.toast(f"🚨 고인용 논문 {len(high_papers)}건 발견!", icon="⚡")
            except Exception as e:
                import traceback
                status.update(label=f"❌ 실패: {e}", state="error")
                st.error(traceback.format_exc())
        st.rerun()

    if bulk_btn and kws:
        prog = st.progress(0)
        total_saved = 0
        all_failed = []
        threshold   = get_high_citation_threshold()
        for i, kw in enumerate(kws):
            try:
                data = get_dashboard_data(kw, threshold)
                total_saved += save_to_db(kw, data["papers"])
                for source, reason in data.get("failed_sources", []):
                    all_failed.append(f"{kw} / {source}: {reason}")
            except Exception:
                pass
            prog.progress((i + 1) / len(kws))
        now      = datetime.now()
        next_run = now + timedelta(hours=get_schedule_hours())
        set_last_run_time(now.strftime("%Y-%m-%d %H:%M:%S"))
        set_next_run_time(next_run.strftime("%Y-%m-%d %H:%M:%S"))
        st.success(f"✅ 전체 수집 완료 · 총 {total_saved}건 저장")
        if all_failed:
            with st.expander(f"⚠️ 수집 실패 소스 {len(all_failed)}건 — 클릭해서 확인"):
                for msg in all_failed:
                    st.warning(msg)
        st.rerun()

    df = get_all_data()
    if not df.empty:
        st.divider()

        m1, m2, m3, m4 = st.columns(4, gap="medium")

        with m1:
            st.markdown(f"""
            <div class="metric-card">
              <div style="display:flex;align-items:center;gap:12px;width:100%;">
                <span style="font-size:1.3rem;">📄</span>
                <div style="flex:1;">
                  <div class="metric-value" style="margin:0;">{len(df):,}</div>
                  <div class="metric-label" style="margin-top:4px;">총 누적 논문</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-card">
              <div style="display:flex;align-items:center;gap:12px;width:100%;">
                <span style="font-size:1.3rem;">🔑</span>
                <div style="flex:1;">
                  <div class="metric-value" style="margin:0;">{len(kws)}</div>
                  <div class="metric-label" style="margin-top:4px;">등록 키워드</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        with m3:
            latest = df['collected_date'].max()[:10] if not df.empty else "-"
            st.markdown(f"""
            <div class="metric-card">
              <div style="display:flex;align-items:center;gap:12px;width:100%;">
                <span style="font-size:1.3rem;">🕒</span>
                <div style="flex:1;">
                  <div class="metric-value-sm" style="margin:0;">{latest}</div>
                  <div class="metric-label" style="margin-top:4px;">최근 업데이트</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        with m4:
            high_count = len(get_high_citation_alerts(100))
            st.markdown(f"""
            <div class="metric-card">
              <div style="display:flex;align-items:center;gap:12px;width:100%;">
                <span style="font-size:1.3rem;">⭐</span>
                <div style="flex:1;">
                  <div class="metric-value" style="margin:0; color:#78BE20;">{high_count}</div>
                  <div class="metric-label" style="margin-top:4px;">고인용 논문</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("### 🏆 인용수 Top 5")
        top5 = (
            df.dropna(subset=['citation_count'])
              .sort_values('citation_count', ascending=False)
              .head(5)
        )
        for rank, (_, row) in enumerate(top5.iterrows(), 1):
            medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][rank - 1]
            link  = row.get('link', '') or ''
            title = str(row.get('title', '제목 없음'))
            journal = row.get('journal', '') or '저널 정보 없음'
            source  = row.get('source', '')
            st.markdown(f"""
            <div class="paper-card">
              <div style="flex:1;min-width:0;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">
                  <span style="font-size:1.05rem;flex-shrink:0;">{medal}</span>
                  <a href="{link}" target="_blank">{title}</a>
                </div>
                <div class="paper-meta">{journal} · {source}</div>
              </div>
              <div style="flex-shrink:0;">
                <span class="badge-citation">{int(row['citation_count'])}회</span>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("👋 아직 수집된 데이터가 없습니다. 위에서 첫 수집을 시작해 보세요!")


# ==================== 페이지: 라이브러리 ====================
elif page == "📚  라이브러리":
    st.subheader("📚 누적 라이브러리")
    df = get_all_data()

    # 라이브러리 내 탭 — 전체 목록 / 즐겨찾기
    lib_tab1, lib_tab2 = st.tabs(["📋 전체 목록", "⭐ 즐겨찾기"])

    # ── 전체 목록 탭 ──────────────────────────────────────────
    with lib_tab1:
      if not df.empty:
        title_search = st.text_input(
            "🔍 논문 제목 검색",
            placeholder="예: glucose, biosensor, CGM ...",
        )

        with st.expander("🎛️ 상세 필터 및 정렬", expanded=False):
            fc1, fc2, fc3 = st.columns(3)

            with fc1:
                journal_search = st.text_input("저널 검색", placeholder="예: Nature, Biosensors")
                max_cit = int(df['citation_count'].max()) if df['citation_count'].notna().any() else 1000
                min_citation, max_citation = st.slider("인용수 범위", 0, max_cit, (0, max_cit))

            with fc2:
                lang_vals    = sorted([x for x in df['language'].dropna().unique()    if x not in ('unknown', '')])
                country_vals = sorted([x for x in df['country'].dropna().unique()     if x not in ('unknown', '')])
                language_filter = st.selectbox("언어", ["전체"] + lang_vals,    disabled=len(lang_vals) == 0)
                country_filter  = st.selectbox("국가", ["전체"] + country_vals, disabled=len(country_vals) == 0)

            with fc3:
                quality_vals = sorted([x for x in df['journal_quality'].dropna().unique() if x not in ('unknown', '')])
                quality_filter  = st.selectbox("저널 급",   ["전체"] + quality_vals, disabled=len(quality_vals) == 0)
                preprint_filter = st.selectbox("출판 유형", ["전체", "정식 출판", "프리프린트"])
                sort_option     = st.selectbox("정렬 기준", ["인용수 높은순", "인용수 낮은순", "최신순", "제목순"])

        filtered_df = df.copy()
        if title_search:
            filtered_df = filtered_df[filtered_df['title'].str.contains(title_search, case=False, na=False)]
        if journal_search:
            filtered_df = filtered_df[filtered_df['journal'].str.contains(journal_search, case=False, na=False)]
        filtered_df = filtered_df[
            (filtered_df['citation_count'] >= min_citation) &
            (filtered_df['citation_count'] <= max_citation)
        ]
        if language_filter != "전체":
            filtered_df = filtered_df[filtered_df['language'] == language_filter]
        if country_filter != "전체":
            filtered_df = filtered_df[filtered_df['country'] == country_filter]
        if quality_filter != "전체":
            filtered_df = filtered_df[filtered_df['journal_quality'] == quality_filter]
        if preprint_filter == "정식 출판":
            filtered_df = filtered_df[filtered_df['is_preprint'] == 0]
        elif preprint_filter == "프리프린트":
            filtered_df = filtered_df[filtered_df['is_preprint'] == 1]

        if sort_option == "인용수 높은순":
            filtered_df = filtered_df.sort_values('citation_count', ascending=False)
        elif sort_option == "인용수 낮은순":
            filtered_df = filtered_df.sort_values('citation_count', ascending=True)
        elif sort_option == "최신순":
            filtered_df = filtered_df.sort_values('collected_date', ascending=False)
        elif sort_option == "제목순":
            filtered_df = filtered_df.sort_values('title', ascending=True)

        res_col, dl_col = st.columns([3, 1])
        with res_col:
            st.markdown(
                f"<span style='font-size:0.88rem;color:#6c757d;'>"
                f"검색 결과 <b style='color:#171c8f;'>{len(filtered_df):,}건</b>"
                f" / 전체 {len(df):,}건</span>",
                unsafe_allow_html=True
            )
        with dl_col:
            if not filtered_df.empty:
                st.download_button(
                    "📥 CSV 다운로드",
                    filtered_df.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"papers_{datetime.now().strftime('%Y%m%d')}.csv",
                    use_container_width=True
                )

        if not filtered_df.empty:
            # 즐겨찾기 버튼을 위해 id 포함해서 표시
            for _, row in filtered_df.head(100).iterrows():
                article_id  = int(row['id'])
                is_starred  = int(row.get('is_starred', 0))
                star_icon   = "⭐" if is_starred else "☆"
                title       = str(row.get('title', '제목 없음'))
                link        = row.get('link', '') or ''
                journal     = row.get('journal', '') or '저널 정보 없음'
                source      = row.get('source', '')
                citation    = int(row['citation_count']) if pd.notna(row['citation_count']) else 0
                memo        = str(row.get('memo', '') or '')

                with st.container():
                    c1, c2 = st.columns([11, 1])
                    with c1:
                        st.markdown(f"""
                        <div class="paper-card">
                          <div style="flex:1;min-width:0;">
                            <a href="{link}" target="_blank">{title}</a>
                            <div class="paper-meta">{journal} · {source}</div>
                            {f'<div style="font-size:0.78rem;color:#78BE20;margin-top:4px;">📝 {memo}</div>' if memo else ''}
                          </div>
                          <span class="badge-citation">{citation}회</span>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        if st.button(star_icon, key=f"star_{article_id}", help="즐겨찾기 토글"):
                            toggle_star(article_id)
                            st.rerun()

                # 메모 입력 (expander)
                with st.expander("📝 메모 보기/편집", expanded=False):
                    new_memo = st.text_area(
                        "메모",
                        value=memo,
                        key=f"memo_{article_id}",
                        height=80,
                        label_visibility="collapsed",
                        placeholder="이 논문에 대한 메모를 입력하세요..."
                    )
                    if st.button("💾 저장", key=f"save_memo_{article_id}"):
                        save_memo(article_id, new_memo)
                        st.toast("메모 저장 완료 ✅")
                        st.rerun()

            if len(filtered_df) > 100:
                st.caption(f"상위 100건만 표시됩니다. 전체 {len(filtered_df):,}건은 CSV 다운로드를 이용하세요.")
        else:
            st.warning("검색 조건에 맞는 논문이 없습니다.")
      else:
        st.info("아직 수집된 데이터가 없습니다. 데이터 수집 탭에서 먼저 수집해 보세요!")

    # ── 즐겨찾기 탭 ───────────────────────────────────────────
    with lib_tab2:
        starred_df = get_starred_articles()
        if not starred_df.empty:
            st.caption(f"총 {len(starred_df)}개의 즐겨찾기 논문")
            # CSV 다운로드
            st.download_button(
                "📥 즐겨찾기 CSV 다운로드",
                starred_df.to_csv(index=False).encode('utf-8-sig'),
                file_name=f"starred_papers_{datetime.now().strftime('%Y%m%d')}.csv",
            )
            for _, row in starred_df.iterrows():
                article_id = int(row['id'])
                title      = str(row.get('title', '제목 없음'))
                link       = row.get('link', '') or ''
                journal    = row.get('journal', '') or '저널 정보 없음'
                source     = row.get('source', '')
                citation   = int(row['citation_count']) if pd.notna(row['citation_count']) else 0
                memo       = str(row.get('memo', '') or '')

                with st.container():
                    c1, c2 = st.columns([11, 1])
                    with c1:
                        st.markdown(f"""
                        <div class="paper-card">
                          <div style="flex:1;min-width:0;">
                            <a href="{link}" target="_blank">{title}</a>
                            <div class="paper-meta">{journal} · {source}</div>
                            {f'<div style="font-size:0.78rem;color:#78BE20;margin-top:4px;">📝 {memo}</div>' if memo else ''}
                          </div>
                          <span class="badge-citation">{citation}회</span>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        if st.button("⭐", key=f"unstar_{article_id}", help="즐겨찾기 해제"):
                            toggle_star(article_id)
                            st.rerun()

                with st.expander("📝 메모 보기/편집", expanded=False):
                    new_memo = st.text_area(
                        "메모",
                        value=memo,
                        key=f"smemo_{article_id}",
                        height=80,
                        label_visibility="collapsed",
                        placeholder="이 논문에 대한 메모를 입력하세요..."
                    )
                    if st.button("💾 저장", key=f"ssave_memo_{article_id}"):
                        save_memo(article_id, new_memo)
                        st.toast("메모 저장 완료 ✅")
                        st.rerun()
        else:
            st.info("⭐ 아직 즐겨찾기한 논문이 없어요. 전체 목록에서 ☆ 버튼을 눌러 추가하세요!")


# ==================== 페이지: 신규 수집 (7일간) ====================
elif page == "🆕  신규 수집":
    st.subheader("🆕 최근 7일간 신규 수집된 논문")
    st.caption("지난 7일 동안 수집된 논문을 최신순으로 보여줍니다")

    df = get_all_data()

    if not df.empty:
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        new_df = df[df['collected_date'] >= seven_days_ago].copy()

        if not new_df.empty:
            new_df = new_df.sort_values('collected_date', ascending=False)
            st.success(f"총 {len(new_df):,}건의 신규 논문이 수집되었습니다.")

            display_df = new_df[['title', 'journal', 'citation_count', 'source', 'collected_date', 'link']].copy()
            display_df['citation_count'] = display_df['citation_count'].apply(
                lambda x: f"{int(x):,}회" if pd.notna(x) else "0회"
            )
            display_df['collected_date'] = display_df['collected_date'].str[:10]

            st.dataframe(
                display_df,
                column_config={
                    "title":          st.column_config.TextColumn("논문 제목", width="large"),
                    "journal":        st.column_config.TextColumn("저널",     width="medium"),
                    "citation_count": st.column_config.TextColumn("인용수", width="small"),
                    "source":         st.column_config.TextColumn("출처",     width="small"),
                    "collected_date": st.column_config.TextColumn("수집일",   width="small"),
                    "link":           st.column_config.LinkColumn("링크", display_text="🔗 열기", width="small"),
                },
                hide_index=True,
                width='stretch',
                height=600,
            )

            csv = new_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 최근 7일 신규 논문 CSV 다운로드",
                csv,
                file_name=f"new_papers_last_7days_{datetime.now().strftime('%Y%m%d')}.csv"
            )
        else:
            st.info("최근 7일간 수집된 논문이 없습니다.")
    else:
        st.info("아직 수집된 데이터가 없습니다.")


# ==================== 페이지: 설정 ====================
elif page == "⚙️  설정":
    st.subheader("⚙️ 환경 설정")
    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown("#### 🔑 키워드 관리")

        # ── 단일 등록 ──
        new_kw = st.text_input("새 키워드 추가", placeholder="예: electrochemical biosensor")
        if st.button("➕ 등록", use_container_width=True):
            if new_kw.strip():
                if add_target_keyword(new_kw):
                    st.toast("추가됨 ✅ — 스케줄러가 다음 실행 시 자동 반영됩니다.")
                    st.rerun()
                else:
                    st.warning("이미 등록된 키워드입니다.")
            else:
                st.error("키워드를 입력해주세요.")

        # ── 일괄 등록 ──
        st.markdown("**📋 일괄 등록** — 줄바꿈 또는 쉼표로 구분해서 입력")
        bulk_input = st.text_area(
            "키워드 목록",
            placeholder="glucose monitoring\ncontinuous glucose monitor\nbiosensor\nHbA1c, CGM, wearable sensor",
            height=120,
            label_visibility="collapsed"
        )
        if st.button("➕ 일괄 등록", use_container_width=True):
            if bulk_input.strip():
                # 줄바꿈과 쉼표 모두 구분자로 처리
                raw = bulk_input.replace(",", "\n")
                candidates = [k.strip() for k in raw.splitlines() if k.strip()]
                added, skipped = [], []
                for kw in candidates:
                    if add_target_keyword(kw):
                        added.append(kw)
                    else:
                        skipped.append(kw)
                if added:
                    st.success(f"✅ {len(added)}개 등록 완료: {', '.join(added)}")
                if skipped:
                    st.warning(f"⚠️ {len(skipped)}개 중복 건너뜀: {', '.join(skipped)}")
                st.rerun()
            else:
                st.error("키워드를 입력해주세요.")

        st.divider()

        # ── 등록된 키워드 목록 ──
        kws_list = get_keywords_list()
        if kws_list:
            for k in kws_list:
                r1, r2 = st.columns([5, 1])
                r1.write(f"• {k}")
                if r2.button("삭제", key=f"del_{k}", type="secondary"):
                    delete_target_keyword(k)
                    st.rerun()
        else:
            st.info("등록된 키워드가 없습니다.")

    with col_b:
        st.markdown("#### ⚙️ 고급 설정")
        current_th = get_high_citation_threshold()
        new_th = st.slider("고인용 임계치 (인용수 기준)", 10, 200, current_th, 5)
        if new_th != current_th:
            if st.button("💾 저장", use_container_width=True):
                set_high_citation_threshold(new_th)
                st.toast(f"{new_th}회로 변경됨", icon="✅")

        st.divider()

        st.markdown("**전체 데이터 초기화**")
        st.warning("⚠️ 수집된 모든 논문 데이터가 삭제됩니다. 되돌릴 수 없어요.")
        confirm = st.checkbox("초기화를 확인했습니다.")
        if confirm:
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if st.button("🗑️ 전체 데이터 초기화", use_container_width=True, disabled=not confirm):
                reset_all_data()
                st.toast("초기화 완료", icon="🗑️")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("© 2026 i-SENS 교육지원 · Sensing Ahead, Caring More")
