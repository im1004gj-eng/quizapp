import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로드 (에러 방지를 위해 try-except 사용)
try:
    users_df = conn.read(worksheet="users", ttl=0)
    quiz_df = conn.read(worksheet="quiz", ttl=0)
except Exception as e:
    st.error("시트를 불러올 수 없습니다. 공유 설정을 확인해주세요.")
    st.stop()

if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("아이디 입력").strip()
    if st.button("시작"):
        if user_id:
            user_row = users_df[users_df['username'].astype(str) == user_id]
            if user_row.empty:
                # 새 유저 추가 시 데이터 타입 강제 지정
                new_data = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                users_df = pd.concat([users_df, new_data], ignore_index=True)
                conn.update(worksheet="users", data=users_df)
                st.session_state.score, st.session_state.stamina = 0, 5
            else:
                st.session_state.score = int(user_row.iloc[0]['score'])
                st.session_state.stamina = int(user_row.iloc[0]['stamina'])
            st.session_state.user = user_id
            st.session_state.solved = []
            st.rerun()
else:
    st.header(f"🎮 {st.session_state.user}님")
    col1, col2 = st.columns(2)
    col1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    col2.metric("🏆 점수", st.session_state.score)

    if st.session_state.stamina <= 0:
        st.warning("스태미너 충전 중... (10초)")
        time.sleep(10)
        st.session_state.stamina = 5
        users_df.loc[users_df['username'].astype(str) == st.session_state.user, 'stamina'] = 5
        conn.update(worksheet="users", data=users_df)
        st.rerun()
    else:
        rem = [i for i in range(len(quiz_df)) if i not in st.session_state.solved]
        if not rem: 
            st.session_state.solved = []
            rem = list(range(len(quiz_df)))
        
        if 'q_idx' not in st.session_state:
            st.session_state.q_idx = random.choice(rem)
        
        q = quiz_df.iloc[st.session_state.q_idx]
        st.info(f"문제: {q.iloc[0]}")
        
        for i in range(1, 5):
            if st.button(str(q.iloc[i]), key=f"ans_{i}", use_container_width=True):
                st.session_state.solved.append(st.session_state.q_idx)
                if str(q.iloc[i]).strip() == str(q.iloc[5]).strip():
                    st.success("정답! +10")
                    st.session_state.score += 10
                else:
                    st.error(f"오답! 정답: {q.iloc[5]}")
                    st.session_state.stamina -= 1
                
                # 시트 업데이트
                users_df.loc[users_df['username'].astype(str) == st.session_state.user, ['score', 'stamina']] = [st.session_state.score, st.session_state.stamina]
                conn.update(worksheet="users", data=users_df)
                del st.session_state.q_idx
                time.sleep(1)
                st.rerun()
