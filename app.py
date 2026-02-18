import streamlit as st
import pandas as pd
import random
import time

st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 1. 구글 시트 ID (공유 설정: 링크가 있는 모든 사용자 - 편집자 필수)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

def load_data(sheet_name):
    # 캐시 방지를 위해 랜덤 파라미터 추가
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}&refresh={random.random()}"
    try:
        df = pd.read_csv(url)
        # 중요: 데이터가 없는 빈 줄(NaN)은 무조건 삭제
        df = df.dropna(subset=[df.columns[0]]) 
        return df
    except:
        return None

# 데이터 로드
quiz_df = load_data("quiz")
users_df = load_data("users")

if 'user' not in st.session_state:
    st.title("🏆 퀴즈 챌린지")
    user_id = st.text_input("닉네임을 입력하세요").strip()
    if st.button("입장"):
        if user_id:
            st.session_state.user = user_id
            st.session_state.score = 0
            st.session_state.stamina = 5
            st.session_state.solved = [] 
            st.rerun()
else:
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    # --- 문제 출제 로직 개선 ---
    # 전체 문제 인덱스 확인
    all_indices = list(range(len(quiz_df)))
    # 아직 안 푼 문제 인덱스
    available = [i for i in all_indices if i not in st.session_state.solved]

    # 만약 남은 문제가 없거나 "한글날"만 반복된다면 리스트 강제 초기화
    if not available:
        st.success("🎉 모든 문제를 정복했습니다! 처음부터 다시 섞어 시작합니다.")
        st.session_state.solved = []
        available = all_indices

    # 현재 문제가 세션에 없거나 이미 푼 문제라면 새로 뽑기
    if 'current_q_idx' not in st.session_state or st.session_state.current_q_idx not in available:
        st.session_state.current_q_idx = random.choice(available)
    
    q_row = quiz_df.iloc[st.session_state.current_q_idx]
    
    st.info(f"문제: {q_row.iloc[0]}")

    # 보기 생성
    for i in range(1, 5):
        if st.button(str(q_row.iloc[i]), key=f"btn_{i}", use_container_width=True):
            # 푼 목록에 추가
            st.session_state.solved.append(st.session_state.current_q_idx)
            
            # 정답 확인
            if str(q_row.iloc[i]).strip() == str(q_row.iloc[5]).strip():
                st.success("✨ 정답입니다!")
                st.session_state.score += 10
            else:
                st.error(f"❌ 오답! 정답: {q_row.iloc[5]}")
                st.session_state.stamina -= 1
            
            # 다음 문제를 위해 현재 인덱스 세션에서 삭제
            if 'current_q_idx' in st.session_state:
                del st.session_state.current_q_idx
            
            time.sleep(1)
            st.rerun()

    # 랭킹 표시
    st.divider()
    st.subheader("📊 실시간 랭킹")
    if users_df is not None:
        ranking = users_df.sort_values(by=users_df.columns[1], ascending=False).head(5)
        st.table(ranking.iloc[:, [0, 1]])
