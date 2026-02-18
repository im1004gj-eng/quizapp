import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

st.set_page_config(page_title="퀴즈 챌린지", layout="centered")

# 1. 연결 설정 (Secrets 사용)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # ttl=0을 주어 캐시 문제 방지, 시트 이름을 명시적으로 읽음
        u_df = conn.read(worksheet="users", ttl=0)
        q_df = conn.read(worksheet="quiz", ttl=0)
        return u_df, q_df
    except Exception as e:
        st.error(f"데이터를 가져오는데 실패했습니다: {e}")
        return None, None

users_df, quiz_df = get_data()

# 데이터 로딩 성공 시에만 실행
if users_df is not None and quiz_df is not None:
    if 'user' not in st.session_state:
        st.title("🔐 퀴즈 로그인")
        user_id = st.text_input("아이디를 입력하세요 (소문자/숫자 권장)")
        if st.button("접속"):
            if user_id:
                # 유저 검색
                user_data = users_df[users_df['username'].astype(str) == str(user_id)]
                
                if user_data.empty:
                    # 신규 유저 생성
                    new_row = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                    users_df = pd.concat([users_df, new_row], ignore_index=True)
                    conn.update(worksheet="users", data=users_df)
                    st.session_state.score, st.session_state.stamina = 0, 5
                else:
                    st.session_state.score = int(user_data.iloc[0]['score'])
                    st.session_state.stamina = int(user_data.iloc[0]['stamina'])
                
                st.session_state.user = user_id
                st.rerun()
    else:
        # --- 게임 메인 화면 ---
        st.header(f"🎮 {st.session_state.user}님의 도전!")
        
        c1, c2 = st.columns(2)
        c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
        c2.metric("🏆 점수", st.session_state.score)

        if st.session_state.stamina <= 0:
            st.warning("스태미너가 없어요! 잠시 후 다시 접속하세요.")
        else:
            if 'q_idx' not in st.session_state:
                st.session_state.q_idx = random.randint(0, len(quiz_df)-1)
            
            q = quiz_df.iloc[st.session_state.q_idx]
            st.info(f"문제: {q['question']}")
            
            # 버튼 레이아웃
            ans_list = [q['opt1'], q['opt2'], q['opt3'], q['opt4']]
            for a in ans_list:
                if st.button(a, use_container_width=True):
                    if str(a) == str(q['answer']):
                        st.success("정답입니다!")
                        st.session_state.score += 10
                    else:
                        st.error(f"틀렸습니다! 정답: {q['answer']}")
                        st.session_state.stamina -= 1
                    
                    # 시트 업데이트
                    users_df.loc[users_df['username'].astype(str) == str(st.session_state.user), ['score', 'stamina']] = [st.session_state.score, st.session_state.stamina]
                    conn.update(worksheet="users", data=users_df)
                    
                    del st.session_state.q_idx
                    time.sleep(1)
                    st.rerun()

        # 랭킹창
        st.divider()
        st.subheader("🏅 실시간 랭킹")
        rank = users_df.sort_values("score", ascending=False).head(5)
        st.dataframe(rank[['username', 'score']], use_container_width=True)
