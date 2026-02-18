import streamlit as st
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 ID (공유 설정이 '편집자'로 되어 있어야 함)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

def load_data(sheet_name):
    # 캐시 방지를 위해 랜덤 파라미터 추가하여 매번 새로 읽음
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}&refresh={random.random()}"
    try:
        df = pd.read_csv(url)
        return df.dropna(subset=[df.columns[0]]) # 빈 줄 제거
    except:
        return None

# 데이터 읽기
quiz_df = load_data("quiz")
users_df = load_data("users")

# 3. 로그인 및 세션 관리
if 'user' not in st.session_state:
    st.title("🏆 퀴즈 챌린지")
    user_id = st.text_input("닉네임을 입력하세요").strip()
    if st.button("입장"):
        if user_id:
            st.session_state.user = user_id
            st.session_state.score = 0
            st.session_state.stamina = 5
            st.session_state.solved = [] # 푼 문제 번호 저장 (중복 방지 핵심)
            st.rerun()
else:
    # --- 상태창 ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    # --- 퀴즈 로직 (이미 푼 문제는 안 나옴) ---
    if quiz_df is not None:
        # 아직 안 푼 문제 인덱스만 추출
        all_q_indices = list(range(len(quiz_df)))
        available = [i for i in all_q_indices if i not in st.session_state.solved]

        if not available:
            st.success("🎉 모든 문제를 정복했습니다! 처음부터 다시 섞습니다.")
            st.session_state.solved = [] # 목록 초기화
            available = all_q_indices

        # 현재 문제 인덱스 결정
        if 'current_idx' not in st.session_state:
            st.session_state.current_idx = random.choice(available)
        
        q_row = quiz_df.iloc[st.session_state.current_idx]
        st.info(f"문제: {q_row.iloc[0]}")

        # 보기 버튼
        for i in range(1, 5):
            if st.button(str(q_row.iloc[i]), key=f"btn_{i}_{st.session_state.current_idx}", use_container_width=True):
                # [핵심] 버튼을 누르는 순간 바로 '푼 목록'에 추가
                st.session_state.solved.append(st.session_state.current_idx)
                
                if str(q_row.iloc[i]).strip() == str(q_row.iloc[5]).strip():
                    st.success("✨ 정답입니다! (+10점)")
                    st.session_state.score += 10
                else:
                    st.error(f"❌ 오답! 정답은 [{q_row.iloc[5]}]")
                    st.session_state.stamina -= 1
                
                # 다음 문제를 위해 현재 인덱스 세션에서 삭제
                del st.session_state.current_idx
                time.sleep(1)
                st.rerun()

    # --- 랭킹 (읽기 전용) ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    if users_df is not None:
        # 점수 기준 정렬
        ranking = users_df.sort_values(by=users_df.columns[1], ascending=False).head(5)
        st.table(ranking.iloc[:, [0, 1]])
