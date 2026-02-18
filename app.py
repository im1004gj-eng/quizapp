import streamlit as st
import pandas as pd
import random
import time
import requests

# 1. 환경 설정
st.set_page_config(page_title="무한 퀴즈 챌린지", layout="centered")

# [⚠️ 필수 수정] 구글 앱스 스크립트 배포 후 받은 URL을 여기에 넣으세요!
DEPLOY_URL = "https://script.google.com/macros/s/AKfycby96yM07oCQaIEmMrd9p-t8kwLhla-kodSB6RsKeDnwEKkbSk4XJAbk_fYBSCjNh22Q/exec"
SHEET_ID = "1myzRfMRdT340grI8LsbXn7rc80fi82DsmPsNdgj2oOg"

# 데이터 로드 함수 (캐시 방지 적용)
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}&refresh={random.random()}"
    try:
        df = pd.read_csv(url)
        return df.dropna(subset=[df.columns[0]])
    except:
        return None

# 데이터 초기 로드
quiz_df = load_data("quiz")
users_df = load_data("users")

# 2. 로그인 및 세션 관리
if 'user' not in st.session_state:
    st.title("🏆 무한 퀴즈 챌린지")
    user_id = st.text_input("아이디(닉네임)를 입력하세요").strip()
    if st.button("게임 시작", use_container_width=True):
        if user_id:
            # 기존 유저 점수 확인
            user_row = users_df[users_df['username'].astype(str) == user_id] if users_df is not None else pd.DataFrame()
            
            st.session_state.user = user_id
            st.session_state.score = int(user_row.iloc[0]['score']) if not user_row.empty else 0
            st.session_state.stamina = int(user_row.iloc[0]['stamina']) if not user_row.empty else 5
            st.session_state.solved = [] # 이번 접속에서 푼 문제 리스트
            st.rerun()

else:
    # --- 상단 UI ---
    st.header(f"🎮 {st.session_state.user}님")
    c1, c2 = st.columns(2)
    c1.metric("⚡ 스태미너", f"{st.session_state.stamina}/5")
    c2.metric("🏆 내 점수", st.session_state.score)

    # --- 퀴즈 로직 (중복 방지 핵심) ---
    if st.session_state.stamina <= 0:
        st.error("⚡ 스태미너 소진! 10초 후 자동 충전됩니다.")
        time.sleep(10)
        st.session_state.stamina = 5
        st.rerun()
    else:
        # 아직 안 푼 문제 인덱스 추출
        total_q = len(quiz_df)
        available = [i for i in range(total_q) if i not in st.session_state.solved]

        if not available:
            st.success("🎉 모든 문제를 풀었습니다! 처음부터 다시 시작합니다.")
            st.session_state.solved = []
            available = list(range(total_q))

        # 현재 문제 선정 (세션 고정)
        if 'q_idx' not in st.session_state:
            st.session_state.q_idx = random.choice(available)
        
        q_row = quiz_df.iloc[st.session_state.current_idx if 'current_idx' in st.session_state else st.session_state.q_idx]
        st.info(f"문제: {q_row.iloc[0]}")

        # 보기 버튼 생성
        # 보기 순서: 1, 2, 3, 4 / 정답: 5
        opts = [q_row.iloc[1], q_row.iloc[2], q_row.iloc[3], q_row.iloc[4]]
        for i, opt in enumerate(opts):
            if st.button(str(opt), key=f"btn_{st.session_state.q_idx}_{i}", use_container_width=True):
                # 푼 목록에 즉시 추가 (중복 방지)
                st.session_state.solved.append(st.session_state.q_idx)
                
                # 정답 체크
                if str(opt).strip() == str(q_row.iloc[5]).strip():
                    st.success("✨ 정답입니다! (+10점)")
                    st.balloons()
                    st.session_state.score += 10
                else:
                    st.error(f"❌ 오답! 정답: {q_row.iloc[5]}")
                    st.session_state.stamina -= 1
                
                # ✍️ [기록 로직] Apps Script를 통한 점수 전송
                if DEPLOY_URL != "여기에_복사한_URL을_넣으세요":
                    try:
                        save_params = {
                            "username": st.session_state.user,
                            "score": st.session_state.score,
                            "stamina": st.session_state.stamina
                        }
                        requests.get(DEPLOY_URL, params=save_params)
                    except:
                        pass # 기록 실패 시에도 게임 진행은 방해하지 않음
                
                # 다음 문제를 위해 현재 인덱스 삭제
                del st.session_state.q_idx
                time.sleep(1.2)
                st.rerun()

    # --- 실시간 랭킹 표시 ---
    st.divider()
    st.subheader("📊 실시간 랭킹 (TOP 5)")
    if users_df is not None:
        # 점수 기준 정렬
        users_df['score'] = pd.to_numeric(users_df['score'], errors='coerce').fillna(0)
        ranking = users_df.sort_values(by="score", ascending=False).head(5)
        st.table(ranking[['username', 'score']])
