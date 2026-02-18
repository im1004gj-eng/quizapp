import streamlit as st
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 정보
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"
QUIZ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=quiz"
USERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users"

# 데이터 로드 (캐시 제거: 실시간 업데이트를 위해)
def load_data(url):
    try:
        # 캐시 방지를 위해 랜덤 파라미터 추가
        return pd.read_csv(f"{url}&nocache={random.random()}")
    except:
        return None

# 초기 데이터 로드
quiz_df = load_data(QUIZ_URL)
users_df = load_data(USERS_URL)

if 'user' not in st.session_state:
    st.title("🏆 퀴즈 챌린지")
    user_id = st.text_input("아이디를 입력하세요").strip()
    if st.button("입장"):
        if user_id:
            st.session_state.user = user_id
            st.session_state.score = 0
            st.session_state.stamina = 5
            st.session_state.solved = [] 
            st.rerun()
else:
    # --- 상태 바 ---
    st.header(f"🎮 {st.session_state.user}님의 도전")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 현재 점수", st.session_state.score)

    # --- 중복 방지 퀴즈 로직 ---
    remaining = [i for i in range(len(quiz_df)) if i not in st.session_state.solved]
    
    if not remaining:
        st.success("🎉 모든 문제를 정복했습니다! 처음부터 다시 시작합니다.")
        st.session_state.solved = []
        remaining = list(range(len(quiz_df)))

    # 현재 문제 선정 (세션에 저장하여 리런 시 변하지 않게 함)
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = random.choice(remaining)
    
    q_row = quiz_df.iloc[st.session_state.current_idx]
    st.info(f"문제: {q_row.iloc[0]}")

    # 보기 버튼 생성
    for i in range(1, 5):
        if st.button(str(q_row.iloc[i]), key=f"btn_{i}", use_container_width=True):
            st.session_state.solved.append(st.session_state.current_idx)
            
            if str(q_row.iloc[i]).strip() == str(q_row.iloc[5]).strip():
                st.success("✨ 정답! +10")
                st.session_state.score += 10
            else:
                st.error(f"❌ 오답! 정답: {q_row.iloc[5]}")
                st.session_state.stamina -= 1
            
            # 다음 문제를 위해 인덱스 제거
            del st.session_state.current_idx
            time.sleep(1)
            st.rerun()

    # --- 실시간 랭킹 (시트 읽기) ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    if users_df is not None:
        # 점수 기준 내림차순 정렬
        rank = users_df.sort_values(by=users_df.columns[1], ascending=False).head(5)
        st.table(rank.iloc[:, [0, 1]]) # 이름과 점수만 표시
