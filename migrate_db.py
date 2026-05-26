import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from sqlalchemy import create_engine
import oracledb

print("🚀 전체 데이터 통합 이사(Migration) 스크립트를 시작합니다...")

# 1. 구글 시트 데이터 로드
print("1️⃣ 구글 시트 데이터 로드 중...")
conn_gs = st.connection("gsheets", type=GSheetsConnection)

# 뒤에 .astype(str) 을 붙여서 모든 데이터를 강제로 문자로 변환합니다.
users_df = conn_gs.read(worksheet="Users").fillna("").astype(str)
bizinfo_df = conn_gs.read(worksheet="BizInfo").fillna("").astype(str)

print(f"✔️ Users {len(users_df)}건, BizInfo {len(bizinfo_df)}건 로드 완료")

# 2. 로컬 CSV 파일 로드
print("2️⃣ CSV 데이터 로드 중...")
csv_file_path = "한국산업기술기획평가원_사업공고 현황.csv"  # 실제 파일명
try:
    # 여기에도 .astype(str) 을 붙여줍니다.
    csv_df = pd.read_csv(csv_file_path).fillna("").astype(str)
    print(f"✔️ CSV 데이터 {len(csv_df)}건 로드 완료")
except Exception as e:
    print(f"⚠️ CSV 파일 로드 실패: {e}")
    csv_df = pd.DataFrame()

# 3. 오라클 데이터베이스 연결 엔진 생성
def get_oracle_connection():
    return oracledb.connect(
        user=st.secrets["oracle"]["user"],
        password=st.secrets["oracle"]["password"],
        dsn=st.secrets["oracle"]["dsn"],
        wallet_location=st.secrets["oracle"]["wallet_location"],
        wallet_password=st.secrets["oracle"]["wallet_password"]
    )

engine = create_engine('oracle+oracledb://', creator=get_oracle_connection)

# 4. 데이터를 오라클로 밀어넣기
print("3️⃣ 오라클 DB로 테이블 복사 중...")
try:
    # 🚨 테이블 이름을 무조건 '소문자'로 변경합니다.
    users_df.to_sql('users_tb', engine, if_exists='replace', index=False)
    print("✔️ 'users_tb' 테이블 이사 성공!")
    
    bizinfo_df.to_sql('bizinfo_tb', engine, if_exists='replace', index=False)
    print("✔️ 'bizinfo_tb' 테이블 이사 성공!")
    
    # CSV 데이터도 소문자로 이사
    if not csv_df.empty:
        csv_df.to_sql('csv_data_tb', engine, if_exists='replace', index=False)
        print("✔️ 'csv_data_tb' 테이블 이사 성공!")
        
    print("🎉 [축하합니다] 모든 데이터가 오라클 클라우드로 안전하게 이사되었습니다!")
except Exception as e:
    print(f"❌ 데이터 이사 중 에러 발생: {e}")