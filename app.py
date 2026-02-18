import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 연결 (Secrets 설정을 사용합니다)
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로드 (ttl=0으로 설정하여 항상 최신 기록을 가져옴)
def load_all_data():
    u_df = conn.read(worksheet="users", ttl=0)
    q_df = conn.read(worksheet="quiz", ttl=0)
    # 빈 줄 제거
    u_df = u_df.dropna(subset=[u_df.columns[0]])
    q_df = q_df.dropna(subset=[q_row.columns[0]]) if not q_df.empty else q_df
    return u_df, q_df

users_df, quiz_df = load_all_data()

# 3. 로그인 및 세션 관리
if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("아이디(닉네임)를 입력하세요").strip()
    if st.button("게임 시작", use_container_width=True):
        if user_id:
            # 기존 유저가 시트에 있는지 확인
            user_row = users_df[users_df['username'].astype(str) == user_id]
            
            if user_row.empty:
                # 🆕 신규 유저라면 시트에 바로 기록
                new_data = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                users_df = pd.concat([users_df, new_data], ignore_index=True)
                conn.update(worksheet="users", data=users_df) # 시트에 쓰기!
                st.session_state.score, st.session_state.stamina = 0, 5
            else:
                # 🔙 기존 유저라면 점수 불러오기
                st.session_state.score = int(user_row.iloc[0]['score'])
                st.session_state.stamina = int(user_row.iloc[0]['stamina'])
            
            st.session_state.user = user_id
            st.session_state.solved = [] # 이번 접속에서 푼 문제 리스트
            st.rerun()

else:
    # --- 상단 UI ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 내 점수", st.session_state.score)

    # --- 중복 방지 퀴즈 로직 ---
    available = [i for i in range(len(quiz_df)) if i not in st.session_state.solved]
    
    if not available:
        st.success("🎉 모든 문제를 풀었습니다! 처음부터 다시 시작합니다.")
        st.session_state.solved = []
        available = list(range(len(quiz_df)))

    if 'q_idx' not in st.session_state:
        st.session_state.q_idx = random.choice(available)
    
    q = quiz_df.iloc[st.session_state.q_idx]
    st.info(f"문제: {q.iloc[0]}")

    # 보기 버튼
    for i in range(1, 5):
        choice = str(q.iloc[i])
        if st.button(choice, key=f"btn_{st.session_state.q_idx}_{i}", use_container_width=True):
            # 푼 문제 저장 (중복 방지)
            st.session_state.solved.append(st.session_state.current_q_idx if 'current_q_idx' in st.session_state else st.session_state.q_idx)
            
            # 정답 체크
            if choice.strip() == str(q.iloc[5]).strip():
                st.success("✨ 정답! (+10점)")
                st.session_state.score += 10
            else:
                st.error(f"❌ 오답! 정답: {q.iloc[5]}")
                st.session_state.stamina -= 1
            
            # ✍️ [핵심] 시트에 점수 실시간 기록(Write)
            # 현재 유저의 행을 찾아 점수와 스태미너 업데이트
            users_df.loc[users_df['username'].astype(str) == st.session_state.user, ['score', 'stamina']] = [st.session_state.score, st.session_state.stamina]
            conn.update(worksheet="users", data=users_df)
            
            del st.session_state.q_idx
            time.sleep(1)
            st.rerun()

    # --- 랭킹 표시 ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    # 점수 기준 정렬
    users_df['score'] = pd.to_numeric(users_df['score'], errors='coerce').fillna(0)
    rank = users_df.sort_values(by="score", ascending=False).head(5)
    st.table(rank[['username', 'score']])
