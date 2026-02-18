import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="퀴즈 챌린지 V3", layout="centered")

# --- 구글 시트 연결 ---
# Streamlit Cloud의 Secrets에 시트 URL을 넣거나 아래처럼 직접 입력 (테스트용)
url = "https://docs.google.com/spreadsheets/d/1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수 ---
def load_data():
    # users 탭과 quiz 탭을 각각 읽어옵니다..
    users = conn.read(spreadsheet=url, worksheet="users")
    quizzes = conn.read(spreadsheet=url, worksheet="quiz")
    return users, quizzes

# --- 앱 로직 시작 ---
users_df, quiz_df = load_data()

if 'user' not in st.session_state:
    st.title("🔐 퀴즈 로그인")
    user_id = st.text_input("아이디를 입력하세요")
    if st.button("접속"):
        if user_id:
            # 기존 유저인지 확인
            user_data = users_df[users_df['username'] == user_id]
            if user_data.empty:
                # 신규 유저 등록 (구글 시트에 추가)
                new_user = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                updated_df = pd.concat([users_df, new_user], ignore_index=True)
                conn.update(spreadsheet=url, worksheet="users", data=updated_df)
                st.session_state.score = 0
                st.session_state.stamina = 5
            else:
                st.session_state.score = int(user_data.iloc[0]['score'])
                st.session_state.stamina = int(user_data.iloc[0]['stamina'])
            
            st.session_state.user = user_id
            st.rerun()

else:
    # --- 메인 게임 화면 ---
    st.write(f"👋 반갑습니다, **{st.session_state.user}**님!")
    
    col1, col2 = st.columns(2)
    col1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    col2.metric("🏆 현재 점수", st.session_state.score)

    # 퀴즈 로직 (랜덤 추출)
    if 'q_idx' not in st.session_state:
        st.session_state.q_idx = random.randint(0, len(quiz_df)-1)
    
    q = quiz_df.iloc[st.session_state.q_idx]
    st.markdown(f"### Q. {q['question']}")
    
    # 보기 버튼
    options = [q['opt1'], q['opt2'], q['opt3'], q['opt4']]
    for opt in options:
        if st.button(opt, use_container_width=True):
            if opt == q['answer']:
                st.success("정답!")
                st.session_state.score += 10
            else:
                st.error(f"오답! 정답은 {q['answer']}")
                st.session_state.stamina -= 1
            
            # DB 업데이트 (점수/스태미너 저장)
            users_df.loc[users_df['username'] == st.session_state.user, ['score', 'stamina']] = [st.session_state.score, st.session_state.stamina]
            conn.update(spreadsheet=url, worksheet="users", data=users_df)
            
            del st.session_state.q_idx # 다음 문제를 위해 인덱스 삭제
            time.sleep(1)
            st.rerun()

    # --- 실시간 랭킹 (DB 기반) ---
    st.divider()
    st.subheader("📊 전체 랭킹 TOP 5")
    ranking_df = users_df.sort_values(by="score", ascending=False).head(5)
    st.table(ranking_df[['username', 'score']])
