import streamlit as st
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 정보 (중요: 이 URL을 님의 시트 주소로 꼭 확인하세요)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"
QUIZ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=quiz"
USERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users"

# 데이터 로드 함수
@st.cache_data(ttl=5)
def load_data(url):
    try:
        return pd.read_csv(url)
    except:
        return None

quiz_df = load_data(QUIZ_URL)
users_df = load_data(USERS_URL)

# 3. 로그인 및 세션 관리
if quiz_df is None or users_df is None:
    st.error("⚠️ 시트를 불러올 수 없습니다! 공유 설정이 '링크가 있는 모든 사용자-편집자'인지 확인해주세요.")
    st.stop()

if 'user' not in st.session_state:
    st.title("🏆 퀴즈 챌린지 로그인")
    user_id = st.text_input("아이디(닉네임)를 입력하세요").strip()
    if st.button("접속", use_container_width=True):
        if user_id:
            st.session_state.user = user_id
            st.session_state.score = 0
            st.session_state.stamina = 5
            st.session_state.solved = [] # 푼 문제 저장
            st.rerun()
else:
    # --- 게임 화면 ---
    st.header(f"🎮 {st.session_state.user}님의 도전")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    if st.session_state.stamina <= 0:
        st.error("⚡ 스태미너 소진! 10초 후 자동 충전됩니다.")
        time.sleep(10)
        st.session_state.stamina = 5
        st.rerun()
    else:
        # 중복 방지 문제 선택
        remaining = [i for i in range(len(quiz_df)) if i not in st.session_state.solved]
        if not remaining:
            st.success("🎉 모든 문제를 풀었습니다! 처음부터 다시 섞습니다.")
            st.session_state.solved = []
            remaining = list(range(len(quiz_df)))

        if 'current_q' not in st.session_state:
            st.session_state.current_q = random.choice(remaining)
        
        q_row = quiz_df.iloc[st.session_state.current_q]
        st.info(f"문제: {q_row.iloc[0]}") # 0번 컬럼: 문제

        # 보기 버튼 (1~4번 컬럼: 보기, 5번 컬럼: 정답)
        for i in range(1, 5):
            if st.button(str(q_row.iloc[i]), key=f"ans_{i}", use_container_width=True):
                st.session_state.solved.append(st.session_state.current_q)
                if str(q_row.iloc[i]).strip() == str(q_row.iloc[5]).strip():
                    st.success("✨ 정답입니다! (+10)")
                    st.session_state.score += 10
                else:
                    st.error(f"❌ 오답! 정답은 [{q_row.iloc[5]}] 입니다.")
                    st.session_state.stamina -= 1
                
                # 다음 문제를 위해 인덱스 삭제 후 리런
                del st.session_state.current_q
                time.sleep(1)
                st.rerun()

    # --- 실시간 랭킹 (읽기 전용) ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    st.dataframe(users_df.sort_values(users_df.columns[1], ascending=False).head(5), hide_index=True)
