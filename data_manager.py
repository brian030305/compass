import os
import base64
import zipfile
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import oracledb
from sqlalchemy import create_engine

# 🚨 [수정됨] 깡통 서버 지갑 압축 해제 및 절대경로(config_dir) 탑재 완료
@st.cache_resource
def get_oracle_engine():
    oracle_user = st.secrets.get("ORACLE_USER", "ADMIN")
    oracle_password = st.secrets.get("ORACLE_PASSWORD", "")
    oracle_dsn = st.secrets.get("ORACLE_DSN", "")
    wallet_password = st.secrets.get("WALLET_PASSWORD", "")
    wallet_base64 = st.secrets.get("WALLET_BASE64", "")
    
    wallet_location = os.path.abspath("./bot_wallet")
    
    if not os.path.exists(wallet_location) and wallet_base64:
        os.makedirs(wallet_location, exist_ok=True)
        with open("bot_wallet.zip", "wb") as f:
            f.write(base64.b64decode(wallet_base64))
        with zipfile.ZipFile("bot_wallet.zip", 'r') as zip_ref:
            zip_ref.extractall(wallet_location)

    def get_connection():
        return oracledb.connect(
            user=oracle_user,
            password=oracle_password,
            dsn=oracle_dsn,
            config_dir=wallet_location,     # 🚨 주소록 위치 강제 고정
            wallet_location=wallet_location,
            wallet_password=wallet_password
        )
    return create_engine('oracle+oracledb://', creator=get_connection)

def fetch_safety_cert_data():
    url = "https://api.odcloud.kr/api/15040703/v1/uddi:9bbbc4ab-d825-401f-b7c2-ff065808acec"
    headers = {'Authorization': f'Infuser {st.secrets["SAFETY_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100'} 
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'제품명': '사업/공고/제품명', '제조사명': '관련기관/제조사'})
        else:
            st.warning(f"국가기술표준원 거절됨 (코드: {response.status_code})")
    except Exception as e:
        st.error(f"국가기술표준원 에러: {e}")
    return pd.DataFrame()

def fetch_mss_data():
    url = "https://api.odcloud.kr/api/3034791/v1/uddi:80a74cfd-55d2-4dd3-81c7-d01567d0b3c4"
    headers = {'Authorization': f'Infuser {st.secrets["MSS_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100', 'returnType': 'JSON'}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'사업명': '사업/공고/제품명', '소관기관': '관련기관/제조사'})
        else:
            st.warning(f"중기부 거절됨 (코드: {response.status_code})")
    except Exception as e:
        st.error(f"중기부 에러: {e}")
    return pd.DataFrame()

def fetch_ktl_data():
    url = "https://api.odcloud.kr/api/15124638/v1/uddi:1c027a3c-13c4-49cc-a138-d84d3bd24624"
    headers = {'Authorization': f'Infuser {st.secrets["KTL_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100', 'returnType': 'JSON'}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'업체기본주소': '사업/공고/제품명', '접수수량': '관련기관/제조사'})
        else:
            st.warning(f"KTL 거절됨 (코드: {response.status_code})")
    except Exception as e:
        st.error(f"KTL 에러: {e}")
    return pd.DataFrame()

def fetch_kiat_data():
    url = "https://api.odcloud.kr/api/15069713/v1/uddi:6a6f31dc-cd7c-4d15-83ad-a5d0f400cc1c"
    headers = {'Authorization': f'Infuser {st.secrets["KIAT_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100', 'returnType': 'JSON'}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'지원시책명': '사업/공고/제품명', '지원기관명': '관련기관/제조사'})
        else:
            st.warning(f"KIAT 거절됨 (코드: {response.status_code})")
    except Exception as e:
        st.error(f"KIAT 에러: {e}")
    return pd.DataFrame()

def fetch_keit_min_data():
    url = "https://api.odcloud.kr/api/15147658/v1/uddi:552afd36-0661-41de-9eb4-c1cd7485c8f4"
    headers = {'Authorization': f'Infuser {st.secrets["KEIT_MIN_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100', 'returnType': 'JSON'}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'부처': '관련기관/제조사', '2024년_사업수': '사업/공고/제품명'}) 
        else:
            st.warning(f"KEIT 부처별 거절됨 (코드: {response.status_code})")
    except Exception as e:
        st.error(f"KEIT 부처별 에러: {e}")
    return pd.DataFrame()

def fetch_keit_rd_data():
    url = "https://api.odcloud.kr/api/15011218/v1/uddi:36cb9d74-b258-47ab-9c4d-bcea5e89e7dc"
    headers = {'Authorization': f'Infuser {st.secrets["KEIT_RD_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100', 'returnType': 'JSON'}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'사업명': '사업/공고/제품명'})
        else:
            st.warning(f"KEIT R&D 거절됨 (코드: {response.status_code})")
    except Exception as e:
        st.error(f"KEIT R&D 에러: {e}")
    return pd.DataFrame()

def get_integrated_data():
    df_safety = fetch_safety_cert_data()
    df_mss = fetch_mss_data()
    df_ktl = fetch_ktl_data()
    df_kiat = fetch_kiat_data()
    df_keit_min = fetch_keit_min_data()
    df_keit_rd = fetch_keit_rd_data()
    
    all_dfs = [df_safety, df_mss, df_ktl, df_kiat, df_keit_min, df_keit_rd]
    valid_dfs = [d for d in all_dfs if not d.empty]
    
    if valid_dfs:
        integrated_df = pd.concat(valid_dfs, ignore_index=True)
        return integrated_df.fillna("") 
    return None

# ==========================================
# 📊 [수정됨] KEIT 사업공고 현황 (이제 오라클 DB에서 읽어옵니다)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_local_keit_announcement():
    """한국산업기술기획평가원_사업공고 현황 데이터 로드 (로컬 CSV -> 오라클 연동)"""
    try:
        engine = get_oracle_engine()
        # 오라클에 올린 'csv_data_tb' 테이블을 통째로 읽어옵니다.
        df = pd.read_sql("SELECT * FROM csv_data_tb", engine)
        return df
    except Exception as e:
        st.error(f"KEIT 사업공고 현황 오라클 DB 로드 실패: {e}")
        return pd.DataFrame()

# ==========================================
# 🌐 통계청 전국사업체조사 API
# ==========================================
@st.cache_data(ttl=86400) 
def fetch_national_business_api():
    """전국사업체조사 공공데이터 API 로드"""
    api_key = st.secrets.get("NATIONAL_BUSINESS_SURVEY_API_KEY", "")
    if not api_key:
        st.warning("전국사업체조사 API 키가 설정되지 않았습니다.")
        return pd.DataFrame()
        
    url = "https://api.odcloud.kr/api/15087673/v1/uddi:32e6d6f0-6d01-4f62-b76e-b0ae5b840573" 
    headers = {'Authorization': f'Infuser {api_key}'}
    params = {'page': '1', 'perPage': '1000'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return pd.DataFrame(data['data'])
            else:
                st.error(f"API 응답 구조 확인 필요: {data}")
                return pd.DataFrame()
        else:
            st.error(f"전국사업체조사 API 통신 에러: HTTP {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"전국사업체조사 데이터 로드 실패: {e}")
        return pd.DataFrame()

# ==========================================
# 🌐 중소벤처기업부 기술개발제품 인증현황 API
# ==========================================
@st.cache_data(ttl=86400)
def fetch_mss_tech_cert_api():
    """기술개발제품 인증현황 공공데이터 API 로드"""
    api_key = st.secrets.get("MSS_TECH_CERT_API_KEY", "")
    if not api_key:
        st.warning("기술개발제품 인증현황 API 키가 설정되지 않았습니다.")
        return pd.DataFrame()
        
    url = "https://api.odcloud.kr/api/3033913/v1/uddi:27bb6889-e56d-4cdc-a222-9f02900c81e7" 
    headers = {'Authorization': f'Infuser {api_key}'}
    params = {'page': '1', 'perPage': '500'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return pd.DataFrame(data['data'])
            else:
                st.error(f"API 응답 구조 확인 필요: {data}")
                return pd.DataFrame()
        else:
            st.error(f"인증현황 API 통신 에러: HTTP {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"인증현황 데이터 로드 실패: {e}")
        return pd.DataFrame()

# ==========================================
# 🌐 [수정됨] 기업마당 (Bizinfo) 데이터 로드 (이제 오라클 DB에서 읽어옵니다)
# ==========================================
@st.cache_data(ttl=1800) 
def fetch_bizinfo_api():
    try:
        engine = get_oracle_engine()
        # 🚨 구글 시트 대신 오라클 DB의 'bizinfo_tb' 방에서 데이터를 즉시 가져옵니다.
        df = pd.read_sql("SELECT * FROM bizinfo_tb", engine)
        
        if df.empty:
            return pd.DataFrame()
            
        # 마감일 필터링 (기존 로직 완벽 유지)
        if 'reqstEndDe' in df.columns:
            df['마감일_계산용'] = pd.to_datetime(df['reqstEndDe'], errors='coerce')
            today = pd.Timestamp(datetime.now().date())
            valid_df = df[(df['마감일_계산용'] >= today) | (df['마감일_계산용'].isna())]
            return valid_df.drop(columns=['마감일_계산용']).head(200).reset_index(drop=True)
        return df.head(200)
            
    except Exception as e:
        st.error(f"오라클 DB(기업마당) 읽기 실패: {e}")
        return pd.DataFrame()
