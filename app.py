import streamlit as st
import random
import time
from datetime import datetime

# --- 설정 (핸드폰용 UI 최적화) ---
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# --- 퀴즈 DB (데이터가 많아질수록 별도 파일로 분리 추천) ---
QUIZ_DATA = [
    {"q": "대한민국의 수도는?", "a": ["서울", "부산", "제주", "인천"], "c": "서울"},
    {"q": "지구에서 가장 큰 바다는?", "a": ["대서양", "인도양", "태평양", "북극해"], "c": "태평양"},
    {"q": "사과를 영어로 하면?", "a": ["Banana", "Apple", "Grape", "Orange"], "c": "Apple"},
    {"q": "가장 가벼운 원소는?", "a": ["산소", "질소", "수소", "탄소"], "c": "수소"},
    {"q": "MBTI 중 성인군자형은?", "a": ["ISFJ", "ENFP", "ISTP", "ESTJ"], "c": "ISFJ"},
    # ... 여기에 퀴즈를 50개, 100개 계속 추가하세요!
]

# --- 로그인 세션 관리 ---
if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    st.title("🔐 로그인")
    user_input = st.text_input("아이디(닉네임)를 입력하세요")
    if st.button("시작하기"):
        if user_input:
            st.session_state.user = user_input
            st.session_state.score = 0
            st.session_state.stamina = 5
            st.rerun()

def main_game():
    # 상단 상태바 (모바일용 가독성)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    with col2:
        st.metric("🏆 내 점수", st.session_state.score)

    if st.session_state.stamina <= 0:
        st.error("⚡ 스태미너 소진! 랭킹을 확인하며 기다리세요.")
        if st.button("무료 충전 (30초 대기)"):
            with st.spinner("충전 중..."):
                time.sleep(5) # MVP용으로 짧게 설정
                st.session_state.stamina = 5
                st.rerun()
        return

    # 퀴즈 무작위 추출
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = random.choice(QUIZ_DATA)

    q = st.session_state.current_quiz
    st.markdown(f"### ❓ {q['q']}")
    
    # 버튼형 선택지 (모바일 터치 최적화)
    for ans in q['a']:
        if st.button(ans, use_container_width=True):
            if ans == q['c']:
                st.success("정답입니다! +10점")
                st.session_state.score += 10
            else:
                st.error(f"오답! 정답은 {q['c']}입니다. (스태미너 -1)")
                st.session_state.stamina -= 1
            
            # 다음 문제 준비
            st.session_state.current_quiz = random.choice(QUIZ_DATA)
            time.sleep(1)
            st.rerun()

    # 실시간 랭킹 (임시 구현 - 구글 시트 연동 시 실제 데이터 반영)
    st.divider()
    st.subheader("📊 실시간 TOP 3")
    st.table([
        {"순위": "1위", "아이디": "퀴즈마스터", "점수": 540},
        {"순위": "2위", "아이디": "열공중", "점수": 320},
        {"순위": "3위", "아이디": st.session_state.user, "점수": st.session_state.score}
    ])

# 실행 로직
if st.session_state.user is None:
    login()
else:
    main_game()
