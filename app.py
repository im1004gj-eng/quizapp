import streamlit as st
import pandas as pd
import random
import time
import requests

# 1. 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# [수정 필요] 방금 복사한 구글 웹 앱 URL을 여기에 붙여넣으세요!
DEPLOY_URL = "https://script.google.com/macros/s/AKfycbxvzD9pgpKrsBJt80U0gFJAhkE64f2WKZrDXDB5oOIfSL519wBb8OvKS_E65n0A-Ac/exec"
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

def load_data(name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={name}&refresh={random.random()}"
    return pd.read_csv(url).dropna(subset=[pd.read_csv(url).columns[0]])

# 데이터 읽기
quiz_df = load_data("quiz")
users_df = load_data("users")

# 2. 로그인
if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("닉네임 입력").strip()
    if st.button("시작"):
        if user_id:
            user_row = users_df[users_df['username'].astype(str) == user_id]
            st.session_state.user = user_id
            st.session_state.score = int(user_row.iloc[0]['score']) if not user_row.empty else 0
            st.session_state.stamina = int(user_row.iloc[0]['stamina']) if not user_row.empty else 5
            st.session_state.solved = []
            st.rerun()
else:
    # --- UI ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    # --- 퀴즈 (중복 방지) ---
    available = [i for i in range(len(quiz_df)) if i not in st.session_state.solved]
    if not available:
        st.success("모든 문제를 풀었습니다! 초기화합니다.")
        st.session_state.solved = []
        available = list(range(len(quiz_df)))

    if 'q_idx' not in st.session_state:
        st.session_state.q_idx = random.choice(available)
    
    q = quiz_df.iloc[st.session_state.q_idx]
    st.info(f"문제: {q.iloc[0]}")

    for i in range(1, 5):
        if st.button(str(q.iloc[i]), key=f"b_{st.session_state.q_idx}_{i}", use_container_width=True):
            st.session_state.solved.append(st.session_state.current_q_idx if 'current_q_idx' in st.session_state else st.session_state.q_idx)
            
            if str(q.iloc[i]).strip() == str(q.iloc[5]).strip():
                st.success("✨ 정답!")
                st.session_state.score += 10
            else:
                st.error(f"❌ 오답! 정답: {q.iloc[5]}")
                st.session_state.stamina -= 1

            # ✍️ [기록 로직] 웹 앱을 통해 점수 전송 (HTTPError 없음!)
            try:
                save_url = f"{DEPLOY_URL}?username={st.session_state.user}&score={st.session_state.score}&stamina={st.session_state.stamina}"
                requests.get(save_url)
            except:
                pass
            
            del st.session_state.q_idx
            time.sleep(1)
            st.rerun()

    # 랭킹
    st.divider()
    st.table(users_df.sort_values(by=users_df.columns[1], ascending=False).head(5).iloc[:, [0, 1]])
