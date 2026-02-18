import streamlit as st
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 URL (CSV 출력 모드)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"
# 캐시를 방지하기 위해 URL 뒤에 랜덤 숫자를 붙이는 함수
def get_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}&refresh={random.random()}"

# 데이터 로드 (캐시 사용 안함)
def load_data():
    q_df = pd.read_csv(get_url("quiz"))
    u_df = pd.read_csv(get_url("users"))
    return q_df, u_df

quiz_df, users_df = load_data()

# 3. 로그인 및 세션 관리
if 'user' not in st.session_state:
    st.title("🏆 퀴즈 챌린지")
    user_id = st.text_input("닉네임을 입력하세요").strip()
    if st.button("입장"):
        if user_id:
            st.session_state.user = user_id
            st.session_state.score = 0
            st.session_state.stamina = 5
            st.session_state.solved = [] # 푼 문제 목록 초기화
            st.rerun()
else:
    # --- 상태창 ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    # --- 문제 출제 (중복 방지 핵심) ---
    # 아직 안 푼 문제 인덱스 찾기
    available_indices = [i for i in range(len(quiz_df)) if i not in st.session_state.solved]
    
    if not available_indices:
        st.success("🎉 모든 문제를 정복했습니다! 처음부터 다시 시작!")
        st.session_state.solved = []
        available_indices = list(range(len(quiz_df)))

    # 현재 문제 설정 (리런해도 안 바뀌게 고정)
    if 'current_q_idx' not in st.session_state:
        st.session_state.current_q_idx = random.choice(available_indices)
    
    q_row = quiz_df.iloc[st.session_state.current_q_idx]
    st.info(f"문제: {q_row.iloc[0]}")

    # 보기 버튼
    for i in range(1, 5):
        if st.button(str(q_row.iloc[i]), key=f"btn_{i}", use_container_width=True):
            # 푼 문제 목록에 추가
            st.session_state.solved.append(st.session_state.current_q_idx)
            
            if str(q_row.iloc[i]).strip() == str(q_row.iloc[5]).strip():
                st.success("✨ 정답! (+10점)")
                st.session_state.score += 10
            else:
                st.error(f"❌ 오답! 정답은 [{q_row.iloc[5]}]")
                st.session_state.stamina -= 1
            
            # 다음 문제를 위해 현재 문제 인덱스 삭제
            del st.session_state.current_q_idx
            time.sleep(1)
            st.rerun()

    # --- 랭킹 표시 ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    if users_df is not None:
        # 점수 기준 정렬하여 상위 5명 출력
        ranking = users_df.sort_values(by=users_df.columns[1], ascending=False).head(5)
        st.table(ranking.iloc[:, [0, 1]])
