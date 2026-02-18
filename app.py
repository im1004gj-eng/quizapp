import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 연결 (Secrets 설정 필수)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_all_data():
    # ttl=0 설정으로 항상 최신 데이터를 읽어옵니다.
    u = conn.read(worksheet="users", ttl=0)
    q = conn.read(worksheet="quiz", ttl=0)
    return u, q

users_df, quiz_df = get_all_data()

# 3. 로그인 로직
if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("아이디를 입력하세요", placeholder="닉네임 입력")
    if st.button("게임 시작", use_container_width=True):
        if user_id:
            # 기존 유저 확인 (공백 제거 후 비교)
            user_row = users_df[users_df['username'].astype(str).str.strip() == user_id.strip()]
            
            if user_row.empty:
                # 신규 등록
                new_data = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                updated_users = pd.concat([users_df, new_data], ignore_index=True)
                conn.update(worksheet="users", data=updated_users)
                st.session_state.score, st.session_state.stamina = 0, 5
            else:
                # 기존 데이터 로드
                st.session_state.score = int(user_row.iloc[0]['score'])
                st.session_state.stamina = int(user_row.iloc[0]['stamina'])
            
            st.session_state.user = user_id
            st.session_state.solved_list = [] # 푼 문제 인덱스 저장
            st.rerun()

else:
    # --- 상단 UI ---
    st.header(f"🎮 {st.session_state.user}님의 도전")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    # --- 퀴즈 로직 (중복 방지) ---
    if st.session_state.stamina <= 0:
        st.error("⚡ 스태미너 소진! 10초 후 자동 충전됩니다.")
        time.sleep(10)
        st.session_state.stamina = 5
        # 시트에도 충전 상태 저장
        users_df.loc[users_df['username'] == st.session_state.user, 'stamina'] = 5
        conn.update(worksheet="users", data=users_df)
        st.rerun()
    else:
        # 안 푼 문제 인덱스 추출
        remaining = [i for i in range(len(quiz_df)) if i not in st.session_state.solved_list]
        
        if not remaining:
            st.success("🎉 모든 문제를 정복했습니다! 처음부터 다시 섞습니다.")
            st.session_state.solved_list = []
            remaining = list(range(len(quiz_df)))

        if 'q_idx' not in st.session_state:
            st.session_state.q_idx = random.choice(remaining)
        
        row = quiz_df.iloc[st.session_state.q_idx]
        st.info(f"문제: {row.iloc[0]}") # 첫 번째 칸: 문제

        # 보기 버튼 생성 (시트 순서: 1~4번 보기, 5번 정답)
        opts = [row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4]]
        for opt in opts:
            if st.button(str(opt), use_container_width=True):
                # 푼 목록 추가
                st.session_state.solved_list.append(st.session_state.q_idx)
                
                # 정답 체크
                if str(opt).strip() == str(row.iloc[5]).strip():
                    st.success("✨ 정
