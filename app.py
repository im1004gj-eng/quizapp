import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# 2. 구글 시트 연결 (Secrets 설정 기반)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ttl=0으로 설정하여 매번 최신 데이터를 읽어옵니다.
    u = conn.read(worksheet="users", ttl=0)
    q = conn.read(worksheet="quiz", ttl=0)
    return u, q

users_df, quiz_df = get_data()

# 3. 로그인 및 세션 초기화
if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("닉네임을 입력하세요").strip()
    if st.button("게임 시작", use_container_width=True):
        if user_id:
            # 기존 유저 확인 (문자열 비교)
            user_row = users_df[users_df['username'].astype(str) == user_id]
            
            if user_row.empty:
                # 신규 유저 등록
                new_user = pd.DataFrame([{"username": user_id, "score": 0, "stamina": 5}])
                users_df = pd.concat([users_df, new_user], ignore_index=True)
                conn.update(worksheet="users", data=users_df)
                st.session_state.score, st.session_state.stamina = 0, 5
            else:
                # 기존 유저 데이터 로드
                st.session_state.score = int(user_row.iloc[0]['score'])
                st.session_state.stamina = int(user_row.iloc[0]['stamina'])
            
            st.session_state.user = user_id
            st.session_state.solved = [] # 푼 문제 인덱스 저장용
            st.rerun()

else:
    # --- 상태 바 ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 점수", st.session_state.score)

    # --- 퀴즈 로직 (중복 방지 핵심) ---
    if st.session_state.stamina <= 0:
        st.error("스태미너 부족! 10초 후 자동 충전됩니다.")
        time.sleep(10)
        st.session_state.stamina = 5
        # 시트 업데이트
        users_df.loc[users_df['username'].astype(str) == st.session_state.user, 'stamina'] = 5
        conn.update(worksheet="users", data=users_df)
        st.rerun()
    else:
        # 아직 안 푼 문제 필터링
        total_q = len(quiz_df)
        available = [i for i in range(total_q) if i not in st.session_state.solved]

        if not available:
            st.success("🎉 모든 문제를 풀었습니다! 처음부터 다시 섞습니다.")
            st.session_state.solved = []
            available = list(range(total_q))

        # 현재 문제 인덱스 결정
        if 'q_idx' not in st.session_state:
            st.session_state.q_idx = random.choice(available)
        
        q_row = quiz_df.iloc[st.session_state.q_idx]
        st.info(f"문제: {q_row.iloc[0]}")

        # 보기 버튼 생성
        opts = [q_row.iloc[1], q_row.iloc[2], q_row.iloc[3], q_row.iloc[4]]
        for opt in opts:
            if st.button(str(opt), key=f"btn_{opt}_{st.session_state.q_idx}", use_container_width=True):
                # 푼 목록에 추가 (중복 방지 핵심)
                st.session_state.solved.append(st.session_state.q_idx)
                
                # 정답 확인
                if str(opt).strip() == str(q_row.iloc[5]).strip():
                    st.success("✨ 정답입니다! (+10점)")
                    st.balloons() # 축하 효과
                    st.session_state.score += 10
                else:
                    st.error(f"❌ 오답! 정답: {q_row.iloc[5]}")
                    st.session_state.stamina -= 1
                
                # --- DB 실시간 업데이트 ---
                # 데이터 타입을 맞춰서 시트에 기록
                users_df.loc[users_df['username'].astype(str) == st.session_state.user, ['score', 'stamina']] = [int(st.session_state.score), int(st.session_state.stamina)]
                conn.update(worksheet="users", data=users_df)
                
                # 다음 문제를 위해 현재 인덱스 삭제 후 새로고침
                del st.session_state.q_idx
                time.sleep(1)
                st.rerun()

    # --- 실시간 랭킹 ---
    st.divider()
    st.subheader("📊 실시간 랭킹 TOP 5")
    # 점수 컬럼을 숫자로 변환 후 정렬
    users_df['score'] = pd.to_numeric(users_df['score'], errors='coerce').fillna(0)
    ranking = users_df.sort_values(by="score", ascending=False).head(5)
    st.table(ranking[['username', 'score']])
