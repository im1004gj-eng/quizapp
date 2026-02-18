import streamlit as st
import pandas as pd
import random
import time

# 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 구글 시트 주소 (님의 시트 ID 사용)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"
USERS_URL = f"https://docs.google.com/spreadsheets/d/{users}/gviz/tq?tqx=out:csv&sheet=users"
QUIZ_URL = f"https://docs.google.com/spreadsheets/d/{quiz}/gviz/tq?tqx=out:csv&sheet=quiz"

@st.cache_data(ttl=5) # 5초마다 데이터 갱신
def load_all_data():
    try:
        u_df = pd.read_csv(USERS_URL)
        q_df = pd.read_csv(QUIZ_URL)
        return u_df, q_df
    except Exception as e:
        st.error(f"시트 탭 이름을 확인해주세요! (users, quiz): {e}")
        return None, None

users_df, quiz_df = load_all_data()

if users_df is not None and quiz_df is not None:
    if 'user' not in st.session_state:
        st.title("🔐 퀴즈 로그인")
        user_id = st.text_input("아이디를 입력하세요")
        if st.button("로그인/가입"):
            if user_id:
                st.session_state.user = user_id
                # MVP 단계에서는 세션에 임시 저장 (시트 쓰기 권한 복잡성 방지)
                st.session_state.score = 0
                st.session_state.stamina = 5
                st.rerun()
    else:
        st.header(f"🎮 {st.session_state.user}님의 도전!")
        
        c1, c2 = st.columns(2)
        c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
        c2.metric("🏆 점수", st.session_state.score)

        if st.session_state.stamina <= 0:
            st.error("스태미너 부족! 광고(5초 대기) 후 충전됩니다.")
            time.sleep(5)
            st.session_state.stamina = 5
            st.rerun()
        else:
            if 'q_idx' not in st.session_state:
                st.session_state.q_idx = random.randint(0, len(quiz_df)-1)
            
            q = quiz_df.iloc[st.session_state.q_idx]
            st.info(f"문제: {q['question']}")
            
            options = [q['opt1'], q['opt2'], q['opt3'], q['opt4']]
            for opt in options:
                if st.button(opt, use_container_width=True):
                    if str(opt) == str(q['answer']):
                        st.success("정답! +10")
                        st.session_state.score += 10
                    else:
                        st.error(f"오답! 정답은 {q['answer']}")
                        st.session_state.stamina -= 1
                    
                    del st.session_state.q_idx
                    time.sleep(1)
                    st.rerun()

        st.divider()
        st.subheader("📊 명예의 전당 (실시간)")
        # 시트 데이터 기반 랭킹
        st.dataframe(users_df.sort_values("score", ascending=False).head(5), use_container_width=True)
