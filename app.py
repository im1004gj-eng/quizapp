import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

# 페이지 설정
st.set_page_config(page_title="퀴즈 챌린지", layout="centered")

# 캐시 삭제 (에러 잔상 제거용 - 한 번 성공하면 지워도 됨)
st.cache_data.clear()

# 구글 시트 연결 (Secrets에 설정된 값을 자동으로 가져옴)
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # worksheet 이름 대신 순서(0, 1)로 읽어오기 (이게 더 확실할 때가 있습니다)
    users_df = conn.read(worksheet="users", ttl=0) # ttl=0은 즉시 업데이트용
    quiz_df = conn.read(worksheet="quiz", ttl=0)

    if 'user' not in st.session_state:
        st.title("🔐 퀴즈 로그인")
        user_id = st.text_input("아이디를 입력하세요")
        if st.button("접속"):
            if user_id:
                user_data = users_df[users_df['username'] == user_id]
                if user_data.empty:
                    new_user = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                    users_df = pd.concat([users_df, new_user], ignore_index=True)
                    conn.update(worksheet="users", data=users_df)
                    st.session_state.score, st.session_state.stamina = 0, 5
                else:
                    st.session_state.score = int(user_data.iloc[0]['score'])
                    st.session_state.stamina = int(user_data.iloc[0]['stamina'])
                st.session_state.user = user_id
                st.rerun()
    else:
        # 게임 화면
        st.write(f"👋 **{st.session_state.user}**님 환영합니다!")
        col1, col2 = st.columns(2)
        col1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
        col2.metric("🏆 점수", st.session_state.score)

        if st.session_state.stamina <= 0:
            st.error("스태미너 부족! 잠시 후 이용하세요.")
        else:
            if 'q_idx' not in st.session_state:
                st.session_state.q_idx = random.randint(0, len(quiz_df)-1)
            
            q = quiz_df.iloc[st.session_state.q_idx]
            st.markdown(f"### Q. {q['question']}")
            
            opts = [q['opt1'], q['opt2'], q['opt3'], q['opt4']]
            for opt in opts:
                if st.button(opt, use_container_width=True):
                    if opt == q['answer']:
                        st.success("정답! +10")
                        st.session_state.score += 10
                    else:
                        st.error(f"오답! 정답: {q['answer']}")
                        st.session_state.stamina -= 1
                    
                    # DB 저장
                    users_df.loc[users_df['username'] == st.session_state.user, ['score', 'stamina']] = [st.session_state.score, st.session_state.stamina]
                    conn.update(worksheet="users", data=users_df)
                    del st.session_state.q_idx
                    time.sleep(1)
                    st.rerun()

        # 랭킹 표시
        st.divider()
        st.subheader("📊 TOP 5 랭킹")
        st.table(users_df.sort_values("score", ascending=False).head(5)[['username', 'score']])

except Exception as e:
    st.error(f"연결 에러 발생: {e}")
    st.info("시트의 탭 이름이 'users'와 'quiz'인지 다시 확인해주세요!")
