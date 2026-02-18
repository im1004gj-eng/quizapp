import streamlit as st
import pandas as pd
import random
import time

st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 1. 구글 시트 ID 확인 (편집자 권한 필수)
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

def load_data(sheet_name):
    # 캐시를 완전히 무시하기 위한 랜덤 파라미터
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}&refresh={random.random()}"
    try:
        # header=0 을 명시하여 첫 번째 줄이 제목임을 알림
        df = pd.read_csv(url, header=0)
        # 데이터 앞뒤 공백 제거 및 빈 줄 완벽 제거
        df = df.dropna(how='all')
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

# 데이터 읽기
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
            st.session_state.solved = [] # 푼 문제 저장 리스트
            st.rerun()
else:
    # --- 상태창 ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 내 점수", st.session_state.score)

    # --- 퀴즈 로직 (강제 전체 인식) ---
    if quiz_df is not None:
        total_questions = len(quiz_df)
        available = [i for i in range(total_questions) if i not in st.session_state.solved]

        # 모든 문제를 풀었을 때만 초기화
        if not available:
            st.success("🎉 시트의 모든 문제를 정복했습니다! 다시 섞습니다.")
            st.session_state.solved = []
            available = list(range(total_questions))

        # 현재 문제 인덱스 결정 (세션에 없으면 새로 뽑기)
        if 'current_idx' not in st.session_state:
            # 시트의 모든 인덱스 중에서 랜덤하게 선택
            st.session_state.current_idx = random.choice(available)
        
        # 문제 가져오기
        q_row = quiz_df.iloc[st.session_state.current_idx]
        
        st.info(f"문제 {st.session_state.current_idx + 1}: {q_row.iloc[0]}")

        # 보기 버튼 생성
        opts = [q_row.iloc[1], q_row.iloc[2], q_row.iloc[3], q_row.iloc[4]]
        for i, opt in enumerate(opts):
            if st.button(str(opt), key=f"btn_{i}", use_container_width=True):
                # 푼 목록에 현재 인덱스 추가
                st.session_state.solved.append(st.session_state.current_q_idx if 'current_q_idx' in st.session_state else st.session_state.current_idx)
                
                # 정답 체크
                if str(opt).strip() == str(q_row.iloc[5]).strip():
                    st.success("✨ 정답입니다!")
                    st.balloons()  # <--- 이 줄 추가! 화면에 풍선이 팡팡 터집니다.
                    st.session_state.score += 10
                else:
                    st.error(f"❌ 오답! 정답: {q_row.iloc[5]}")
                    st.session_state.stamina -= 1
                
                # 세션에서 현재 인덱스 제거하여 다음 문제로 넘어가게 함
                if 'current_idx' in st.session_state: del st.session_state.current_idx
                time.sleep(1)
                st.rerun()

    # --- 랭킹 ---
    st.divider()
    st.subheader("📊 실시간 랭킹")
    if users_df is not None:
        ranking = users_df.sort_values(by=users_df.columns[1], ascending=False).head(5)
        st.table(ranking.iloc[:, [0, 1]])
