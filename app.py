import streamlit as st
import pandas as pd
import random
import time

# 페이지 설정 (모바일 최적화)
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 1. 시트 ID 설정 (님의 시트 주소에서 가져옴)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

# 2. 데이터 로드 함수 (탭 이름만 맞으면 무조건 작동)
@st.cache_data(ttl=1)
def load_data(sheet_name):
    # 구글 시트를 CSV 형식으로 바로 읽어오는 URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"'{sheet_name}' 탭을 읽지 못했습니다. 시트 하단 이름을 확인해주세요!")
        return None

# 데이터 읽기 시도
users_df = load_data("users")
quiz_df = load_data("quiz")

# 3. 메인 로직
if users_df is not None and quiz_df is not None:
    if 'user' not in st.session_state:
        st.title("🏆 무한 퀴즈 챌린지")
        user_id = st.text_input("아이디를 입력하세요")
        if st.button("게임 시작"):
            if user_id:
                st.session_state.user = user_id
                st.session_state.score = 0
                st.session_state.stamina = 5
                st.rerun()
    else:
        st.header(f"🎮 {st.session_state.user}님 환영합니다!")
        
        col1, col2 = st.columns(2)
        col1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
        col2.metric("🏆 점수", st.session_state.score)

        if st.session_state.stamina <= 0:
            st.warning("스태미너 부족! 5초 후 자동 충전됩니다.")
            time.sleep(5)
            st.session_state.stamina = 5
            st.rerun()
        else:
            # 문제 랜덤 선택 (인덱스 에러 방지용)
            if 'q_idx' not in st.session_state:
                st.session_state.q_idx = random.randint(0, len(quiz_df) - 1)
            
            q = quiz_df.iloc[st.session_state.q_idx]
            st.info(f"문제: {q['question']}")
            
            # 보기 버튼 생성
            opts = [q['opt1'], q['opt2'], q['opt3'], q['opt4']]
            for opt in opts:
                if st.button(opt, use_container_width=True):
                    if str(opt) == str(q['answer']):
                        st.success("정답입니다! +10점")
                        st.session_state.score += 10
                    else:
                        st.error(f"오답! 정답은 [{q['answer']}] 입니다.")
                        st.session_state.stamina -= 1
                    
                    del st.session_state.q_idx
                    time.sleep(1)
                    st.rerun()

        # 랭킹 표시 (시트 데이터 기반)
        st.divider()
        st.subheader("📊 실시간 랭킹 (전체 유저)")
        if 'score' in users_df.columns:
            rank = users_df.sort_values("score", ascending=False).head(5)
            st.dataframe(rank[['username', 'score']], use_container_width=True, hide_index=True)
