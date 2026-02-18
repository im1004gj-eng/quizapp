import streamlit as st
import pandas as pd
import random
import time

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 ID 설정
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

# 3. 데이터 로드 함수 (CSV 주소 방식)
@st.cache_data(ttl=1)
def load_data(sheet_name):
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        return pd.read_csv(csv_url)
    except Exception as e:
        return None

# 데이터 읽기
users_df = load_data("users")
quiz_df = load_data("quiz")

# 메인 실행 로직
if users_df is not None and quiz_df is not None:
    # --- 로그인 화면 ---
    if 'user' not in st.session_state:
        st.title("🏆 무한 퀴즈 챌린지")
        st.write("아이디를 입력하고 퀴즈를 시작하세요!")
        user_id = st.text_input("아이디 (닉네임)", placeholder="예: 정규진")
        if st.button("게임 입장", use_container_width=True):
            if user_id:
                st.session_state.user = user_id
                st.session_state.score = 0
                st.session_state.stamina = 5
                st.rerun()
    
    # --- 게임 본 화면 ---
    else:
        st.header(f"🎮 {st.session_state.user}님의 도전")
        
        # 상태 표시창
        col1, col2 = st.columns(2)
        col1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
        col2.metric("🏆 내 점수", st.session_state.score)

        st.divider()

        # 스태미너 체크
        if st.session_state.stamina <= 0:
            st.error("⚡ 스태미너를 모두 소진했습니다! 10초 후 자동 충전됩니다.")
            with st.spinner("에너지를 모으는 중..."):
                time.sleep(10)
                st.session_state.stamina = 5
                st.rerun()
        else:
            # 문제 랜덤 선택 (인덱스 유지)
            if 'q_idx' not in st.session_state:
                st.session_state.q_idx = random.randint(0, len(quiz_df) - 1)
            
            # 문제 데이터 추출 (컬럼 이름 대신 '순서' 사용)
            # 순서: 0(문제), 1(보기1), 2(보기2), 3(보기3), 4(보기4), 5(정답)
            row = quiz_df.iloc[st.session_state.q_idx]
            
            question = row.iloc[0]
            options = [row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4]]
            correct_ans = str(row.iloc[5]).strip() # 공백 제거 후 문자열 비교

            st.subheader(f"Q. {question}")

            # 보기 버튼 생성
            for opt in options:
                if st.button(str(opt), use_container_width=True):
                    if str(opt).strip() == correct_ans:
                        st.success("✨ 정답입니다! (+10점)")
                        st.session_state.score += 10
                    else:
                        st.error(f"❌ 틀렸습니다! 정답은 [{correct_ans}] 입니다.")
                        st.session_state.stamina -= 1
                    
                    # 다음 문제를 위해 세션 인덱스 삭제 후 리런
                    del st.session_state.q_idx
                    time.sleep(1.5)
                    st.rerun()

        # --- 하단 실시간 랭킹 ---
        st.divider()
        st.subheader("📊 실시간 랭킹 TOP 5")
        # 0번 컬럼(이름), 1번 컬럼(점수) 가정
        if not users_df.empty:
            # 점수 기준 정렬
            try:
                rank = users_df.sort_values(users_df.columns[1], ascending=False).head(5)
                st.table(rank.iloc[:, [0, 1]])
            except:
                st.write("아직 랭킹 데이터가 없습니다.")

else:
    st.error("구글 시트 연결에 실패했습니다. 탭 이름(users, quiz)을 다시 확인해주세요!")
