import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    u_df = conn.read(worksheet="users", ttl=0)
    q_df = conn.read(worksheet="quiz", ttl=0)
    return u_df, q_df

users_df, quiz_df = load_data()

# 3. 로그인 및 세션 초기화
if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("아이디를 입력하세요")
    if st.button("게임 시작"):
        if user_id:
            user_row = users_df[users_df['username'] == user_id]
            if user_row.empty:
                new_user = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                users_df = pd.concat([users_df, new_user], ignore_index=True)
                conn.update(worksheet="users", data=users_df)
                st.session_state.score, st.session_state.stamina = 0, 5
            else:
                st.session_state.score = int(user_row.iloc[0]['score'])
                st.session_state.stamina = int(user_row.iloc[0]['stamina'])
            
            st.session_state.user = user_id
            st.session_state.solved_indices = [] # 푼 문제 번호 저장용
            st.rerun()

else:
    # --- 상단 상태 표시 ---
    st.header(f"🎮 {st.session_state.user}님의 도전")
    col1, col2 = st.columns(2)
    col1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    col2.metric("🏆 내 점수", st.session_state.score)

    # --- 퀴즈 로직 (중복 방지 핵심) ---
    if st.session_state.stamina <= 0:
        st.error("스태미너 부족! 잠시 후 다시 시도하세요.")
    else:
        # 아직 풀지 않은 문제 번호 리스트 만들기
        available_indices = [i for i in range(len(quiz_df)) if i not in st.session_state.solved_indices]
        
        # 모든 문제를 다 풀었다면 리스트 초기화
        if not available_indices:
            st.success("🎉 모든 문제를 다 풀었습니다! 문제를 다시 섞습니다.")
            st.session_state.solved_indices = []
            available_indices = list(range(len(quiz_df)))

        # 새로운 문제 뽑기
        if 'q_idx' not in st.session_state:
            st.session_state.q_idx = random.choice(available_indices)
        
        q = quiz_df.iloc[st.session_state.q_idx]
        st.info(f"문제: {q.iloc[0]}")
        
        opts = [q.iloc[1], q.iloc[2], q.iloc[3], q.iloc[4]]
        for opt in opts:
            if st.button(str(opt), use_container_width=True):
                # 푼 문제 리스트에 추가 (중복 방지)
                st.session_state.solved_indices.append(st.session_state.q_idx)
                
                if str(opt).strip() == str(q.iloc[5]).strip():
                    st.success("✨ 정답입니다! (+10점)")
                    st.session_state.score += 10
                else:
                    st.error(f"❌ 틀렸습니다! 정답은 [{q.iloc[5]}] 입니다.")
                    st.session_state.stamina -= 1
                
                # --- DB 실시간 기록 업데이트 ---
                users_df.loc[users_df['username'] == st.session_state.user, ['score', 'stamina']] = [st.session_state.score, st.session_state.stamina]
                conn.update(worksheet="users", data=users_df)
                
                del st.session_state.q_idx # 다음 문제를 위해 삭제
                time.sleep(1.2)
                st.rerun()

    # --- 실시간 랭킹 ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    rank_df = users_df.sort_values("score", ascending=False).head(5)
    st.table(rank_df[['username', 'score']])
