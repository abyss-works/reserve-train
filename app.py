"""
app.py — KTX 예매 도우미 (Streamlit)

Korail 계정으로 로그인하여 KTX 열차를 조회하고 예약한다.
"""

import os
from datetime import datetime, date, time

import streamlit as st

from ktx import (
    KorailClient, AuthError, NoResults, SoldOut, NetworkError, KorailClientError,
    TrainInfo, ReservationInfo,
)

# ─── 페이지 설정 ───────────────────────────────────────

st.set_page_config(
    page_title="KTX 예매 도우미",
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 세션 상태 초기화 ─────────────────────────────────

if "client" not in st.session_state:
    st.session_state.client = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_train_idx" not in st.session_state:
    st.session_state.selected_train_idx = None
if "reservation_result" not in st.session_state:
    st.session_state.reservation_result = None
if "page" not in st.session_state:
    st.session_state.page = "search"


# ─── 클라이언트 초기화 (cached) ──────────────────────

@st.cache_resource
def get_client() -> KorailClient:
    """싱글톤 KorailClient 인스턴스"""
    return KorailClient()


def do_login(korail_id: str, korail_pw: str) -> bool:
    """로그인 처리"""
    client = get_client()
    try:
        client.login(korail_id, korail_pw)
        st.session_state.client = client
        st.session_state.logged_in = True
        st.session_state.user_name = client.user_name or ""
        return True
    except AuthError as e:
        st.error(f"로그인 실패: {e}")
    except NetworkError as e:
        st.error(f"네트워크 오류: {e}")
    except KorailClientError as e:
        st.error(f"오류: {e}")
    return False


# ─── 사이드바 ──────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🚄 KTX 예매 도우미")

    if not st.session_state.logged_in:
        st.markdown("---")
        with st.form("login_form"):
            korail_id = st.text_input(
                "Korail ID",
                placeholder="회원번호 / 이메일 / 전화번호",
                value=os.getenv("KORAIL_ID", ""),
            )
            korail_pw = st.text_input(
                "비밀번호",
                type="password",
                placeholder="********",
                value=os.getenv("KORAIL_PW", ""),
            )
            submitted = st.form_submit_button("🔑 로그인", use_container_width=True)

            if submitted and korail_id and korail_pw:
                if do_login(korail_id, korail_pw):
                    st.rerun()
            elif submitted:
                st.warning("ID와 비밀번호를 입력해주세요")

        st.caption("※ 로그인 정보는 서버에 저장되지 않습니다")
    else:
        st.markdown(f"**👤 {st.session_state.user_name or '회원'}**")
        if st.button("🚪 로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.client = None
            st.session_state.search_results = []
            st.session_state.reservation_result = None
            get_client.clear()
            st.rerun()

    st.markdown("---")
    st.caption("v0.1.0 · korail2 기반")


# ─── 메인 영역 ─────────────────────────────────────────

st.title("🚄 KTX 예매 도우미")

if not st.session_state.logged_in:
    # 비로그인 상태: 안내 메시지
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### Korail 계정으로 로그인해주세요

        왼쪽 사이드바에서 Korail ID와 비밀번호를 입력하면
        열차 조회, 예약, 내역 확인을 사용할 수 있습니다.

        - **KTX** 열차 조회 및 예약
        - 예약 내역 확인 및 취소
        - 예약 후 결제는 코레일 앱/웹에서 직접 해주세요
        """)

        st.markdown("---")
        st.markdown("##### 📌 참고")
        st.caption(
            "- 로그인 정보는 세션에만 저장되며, 별도로 저장되지 않습니다\n"
            "- 예약 후 **10분 이내** 결제하지 않으면 자동 취소됩니다\n"
            "- SRT(수서고속철)는 지원하지 않습니다"
        )
else:
    # 로그인 상태: 탭 구성
    tab1, tab2, tab3 = st.tabs(["🔍 열차 조회", "📋 예약 내역", "ℹ️ 사용 안내"])

    # ── Tab 1: 열차 조회 ─────────────────────────────
    with tab1:
        col_search, col_result = st.columns([1, 2])

        with col_search:
            st.markdown("#### 조회 조건")

            with st.form("search_form"):
                dep = st.text_input("출발역", "서울")
                arr = st.text_input("도착역", "부산")

                today = date.today()
                dep_date = st.date_input("출발일", today, min_value=today)

                dep_time = st.time_input("출발 시각 이후", time(9, 0))

                passengers = st.number_input("성인 인원", min_value=1, max_value=9, value=1)

                train_type = st.selectbox(
                    "열차 종류",
                    options=[
                        ("KTX", "ktx"),
                        ("KTX-산천", "ktx-sancheon"),
                        ("ITX-청춘", "itx-cheongchun"),
                        ("ITX-새마을", "itx-saemaeul"),
                        ("무궁화호", "mugunghwa"),
                        ("전체", "all"),
                    ],
                    format_func=lambda x: x[0],
                )

                col_opts1, col_opts2 = st.columns(2)
                with col_opts1:
                    inc_no_seats = st.checkbox("매진 열차 포함", value=False)
                with col_opts2:
                    inc_waiting = st.checkbox("예약대기 포함", value=False)

                searched = st.form_submit_button("🔍 조회", use_container_width=True)

            if searched:
                with st.spinner("열차를 조회하는 중..."):
                    try:
                        client = st.session_state.client
                        results = client.search(
                            dep=dep.strip(),
                            arr=arr.strip(),
                            date=dep_date.strftime("%Y%m%d"),
                            time=dep_time.strftime("%H%M%S"),
                            train_type=train_type[1],
                            passengers=passengers,
                            include_no_seats=inc_no_seats,
                            include_waiting_list=inc_waiting,
                        )
                        st.session_state.search_results = results
                        st.session_state.selected_train_idx = None
                        st.session_state.reservation_result = None
                        st.success(f"✅ {len(results)}건의 열차를 찾았습니다")
                    except NoResults as e:
                        st.session_state.search_results = []
                        st.info(str(e))
                    except AuthError as e:
                        st.error(f"인증 오류: {e}")
                        st.session_state.logged_in = False
                        st.rerun()
                    except (NetworkError, KorailClientError) as e:
                        st.error(str(e))

        with col_result:
            st.markdown("#### 조회 결과")

            results = st.session_state.search_results
            if not results:
                if searched:
                    st.info("조회 결과가 없습니다. 조건을 변경해보세요.")
                else:
                    st.caption("왼쪽에서 조건을 입력하고 조회 버튼을 눌러주세요.")
            else:
                # 데이터프레임 표시
                rows = []
                for i, t in enumerate(results):
                    general = "🟢 가능" if t.general_available else ("🟡 대기" if t.waiting_possible else "🔴 매진")
                    special = "🟢 가능" if t.special_available else ("🔴 매진" if not t.special_available and t.train_type in ("KTX", "KTX-산천") else "-")
                    rows.append({
                        "선택": i,
                        "열차": f"{t.train_type} {t.train_no}",
                        "출발": f"{t.dep_name} {t.dep_display}",
                        "도착": f"{t.arr_name} {t.arr_display}",
                        "소요시간": t.duration,
                        "일반실": general,
                        "특실": special,
                    })

                st.dataframe(
                    rows,
                    column_config={
                        "선택": st.column_config.NumberColumn(width=50),
                        "열차": st.column_config.TextColumn(width=120),
                        "출발": st.column_config.TextColumn(width=140),
                        "도착": st.column_config.TextColumn(width=140),
                        "소요시간": st.column_config.TextColumn(width=80),
                        "일반실": st.column_config.TextColumn(width=90),
                        "특실": st.column_config.TextColumn(width=90),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

                # 열차 선택 및 예약
                st.markdown("---")
                st.markdown("#### 예약할 열차 선택")

                train_options = [
                    f"[{i+1}] {t.train_type} {t.train_no} — "
                    f"{t.dep_name}({t.dep_display})→{t.arr_name}({t.arr_display})"
                    for i, t in enumerate(results)
                ]

                selected_label = st.selectbox(
                    "열차를 선택하세요",
                    options=train_options,
                    index=None,
                    placeholder="열차를 선택해주세요",
                )

                if selected_label:
                    selected_idx = train_options.index(selected_label)
                    st.session_state.selected_train_idx = selected_idx
                    train = results[selected_idx]

                    st.markdown(f"""
                    **선택한 열차:** {train.train_type} {train.train_no}
                    **구간:** {train.dep_name}({train.dep_display}) → {train.arr_name}({train.arr_display})
                    **일반실:** {'🟢 가능' if train.general_available else '🔴 매진'}
                    **특실:** {'🟢 가능' if train.special_available else '🔴 매진'}
                    """)

                    seat_opt = st.radio(
                        "좌석 옵션",
                        options=[
                            ("일반실 우선", "general-first"),
                            ("일반실만", "general-only"),
                            ("특실 우선", "special-first"),
                            ("특실만", "special-only"),
                        ],
                        format_func=lambda x: x[0],
                        horizontal=True,
                    )

                    try_wait = st.checkbox("매진 시 예약대기 신청", value=False)

                    if st.button("✅ 예약하기", type="primary", use_container_width=True):
                        with st.spinner("예약을 진행하는 중..."):
                            try:
                                rsv = client.reserve(
                                    train,
                                    seat_option=seat_opt[1],
                                    passengers=passengers,
                                    try_waiting=try_wait,
                                )
                                st.session_state.reservation_result = rsv
                                st.rerun()
                            except SoldOut as e:
                                st.error(f"매진: {e}")
                            except AuthError as e:
                                st.error(f"인증 오류: {e}")
                                st.session_state.logged_in = False
                                st.rerun()
                            except (NetworkError, KorailClientError) as e:
                                st.error(str(e))

        # 예약 성공 결과 표시
        if st.session_state.reservation_result:
            rsv = st.session_state.reservation_result
            st.markdown("---")
            st.success("### ✅ 예약 완료!")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(f"""
                **예약번호:** `{rsv.rsv_id}`
                **열차:** {rsv.train_type} {rsv.train_no}
                **구간:** {rsv.dep_name}({rsv.dep_display}) → {rsv.arr_name}({rsv.arr_display})
                """)
            with col_r2:
                st.markdown(f"""
                **운임:** {rsv.price:,}원
                **좌석:** {rsv.seat_count}석
                **구입기한:** ⏰ {rsv.limit_display}까지
                """)
            st.warning(
                "⚠️ **결제는 코레일 앱 또는 웹사이트에서 직접 해주세요.**\n\n"
                "구입기한 내에 결제하지 않으면 예약이 자동 취소됩니다."
            )
            if st.button("🔄 새 예약하기"):
                st.session_state.reservation_result = None
                st.session_state.selected_train_idx = None
                st.rerun()

    # ── Tab 2: 예약 내역 ─────────────────────────────
    with tab2:
        st.markdown("#### 내 예약 내역")

        if "my_reservations" not in st.session_state:
            st.session_state.my_reservations = None

        col_btn, col_status = st.columns([1, 3])
        with col_btn:
            refresh_clicked = st.button("🔄 내역 불러오기", use_container_width=False)
        with col_status:
            if st.session_state.my_reservations is not None:
                st.caption(f"총 {len(st.session_state.my_reservations)}건")

        if refresh_clicked or st.session_state.my_reservations is None:
            with st.spinner("예약 내역을 불러오는 중..."):
                try:
                    client = st.session_state.client
                    st.session_state.my_reservations = client.reservations()
                except AuthError as e:
                    st.warning(f"예약 내역을 불러올 수 없습니다: {e}")
                    st.session_state.my_reservations = []
                except (NetworkError, KorailClientError) as e:
                    st.warning(str(e))
                    st.session_state.my_reservations = []

        my_rsvs = st.session_state.my_reservations
        if not my_rsvs:
            st.info("📭 현재 예약 내역이 없습니다")
        else:
            for i, r in enumerate(my_rsvs):
                with st.container(border=True):
                    col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
                    with col_r1:
                        st.markdown(f"""
                        **{r.train_type} {r.train_no}**
                        {r.dep_name}({r.dep_display}) → {r.arr_name}({r.arr_display})
                        """)
                    with col_r2:
                        st.markdown(f"""
                        {r.price:,}원 ({r.seat_count}석)
                        구입기한: {r.limit_display}
                        """)
                    with col_r3:
                        if st.button("❌ 취소", key=f"cancel_{i}", type="secondary"):
                            try:
                                client.cancel(r)
                                st.success(f"예약 {r.rsv_id} 취소 완료")
                                st.rerun()
                            except AuthError as e:
                                st.error(f"인증 오류: {e}")
                                st.session_state.logged_in = False
                                st.rerun()
                            except (NetworkError, KorailClientError) as e:
                                st.error(str(e))

    # ── Tab 3: 안내 ─────────────────────────────────
    with tab3:
        st.markdown("""
        ### ℹ️ KTX 예매 도우미 사용 안내

        **지원 기능:**
        - KTX 열차 조회 (출발역/도착역/날짜/시간)
        - 실시간 좌석 확인 (일반실/특실)
        - 열차 예약
        - 예약 내역 확인 및 취소

        **지원하지 않는 기능:**
        - ❌ 결제 (코레일 앱/웹사이트에서 직접 결제 필요)
        - ❌ SRT (수서고속철)
        - ❌ 회원가입 / 비밀번호 찾기

        **주의사항:**
        - 예약 후 **10분 이내** 결제하지 않으면 자동 취소됩니다
        - 로그인 정보는 서버에 저장되지 않습니다
        - 코레일 API 정책 변경으로 일부 기능이 제한될 수 있습니다

        **기술 정보:**
        - Python korail2 라이브러리 기반
        - Streamlit 웹 UI
        - Docker + K3s 클러스터 배포
        """)

# ─── 하단 정보 ─────────────────────────────────────────

st.markdown("---")
st.caption(
    "KTX 예매 도우미 · korail2 기반 · "
    "예약 후 결제는 코레일 앱/웹에서 직접 해주세요"
)
