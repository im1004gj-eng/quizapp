import streamlit as st
import time

# 1. 초기 데이터 세팅 (실제 서비스 시 DB 연결 필요)
if 'stamina' not in st.session_state:
    st.session_state.stamina = 5
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_index' not in st.session_state:
    st.session_state.quiz_index = 0

# 퀴즈 샘플 데이터
quizzes = [
    {"q": "대한민국의 수도는?", "a": ["서울", "부산", "제주", "인천"], "correct": 0},
    {"q": "지구에서 가장 큰 바다는?", "a": ["대서양", "인도양", "태평양", "북극해"], "correct": 2},
    # 여기에 AI로 생성한 문제 10개를 쭉 넣으면 됩니다.
]

# 2. UI 구성
st.title("🏆 무한 퀴즈 챌린지")
st.sidebar.header(f"⚡ 스태미너: {st.session_state.stamina}/5")
st.sidebar.write(f"⭐ 현재 점수: {st.session_state.score}")

# 3. 게임 로직
if st.session_state.stamina <= 0:
    st.error("⚡ 스태미너가 부족합니다! 잠시 후 다시 시도하세요.")
    if st.button("스태미너 충전하기 (광고 보기 시뮬레이션)"):
        with st.spinner('충전 중...'):
            time.sleep(2)
            st.session_state.stamina = 5
            st.rerun()
else:
    # 퀴즈 출력
    if st.session_state.quiz_index < len(quizzes):
        item = quizzes[st.session_state.quiz_index]
        st.subheader(f"Q{st.session_state.quiz_index + 1}. {item['q']}")
        
        ans = st.radio("정답을 고르세요:", item['a'], key=f"q_{st.session_state.quiz_index}")
        
        if st.button("정답 제출"):
            if item['a'].index(ans) == item['correct']:
                st.success("정답입니다! +10점")
                st.session_state.score += 10
            else:
                st.error("틀렸습니다! 스태미너 -1")
                st.session_state.stamina -= 1
            
            st.session_state.quiz_index += 1
            st.rerun()
    else:
        st.balloons()
        st.write("🎉 모든 문제를 풀었습니다!")
        if st.button("처음부터 다시 하기"):
            st.session_state.quiz_index = 0
            st.rerun()

# 4. 실시간 랭킹 (가상 데이터)
st.divider()
st.subheader("📊 실시간 랭킹 TOP 3")
st.table([
    {"순위": 1, "닉네임": "퀴즈왕", "점수": 1200},
    {"순위": 2, "닉네임": "나야나", "점수": 850},
    {"순위": 3, "닉네임": "도전자", "점수": st.session_state.score}
])
