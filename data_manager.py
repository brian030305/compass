import streamlit as st
import oracledb
import pandas as pd
import requests
from datetime import datetime

# 🚨 지갑 파일 없이 시크릿 정보 3개만으로 연결합니다!
def get_oracle_engine():
    return oracledb.connect(
        user=st.secrets["ORACLE_USER"],
        password=st.secrets["ORACLE_PASSWORD"],
        dsn=st.secrets["ORACLE_DSN"]
    )

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

@st.cache_data(ttl=3600)
def fetch_local_keit_announcement():
    try:
        engine = get_oracle_engine()
        df = pd.read_sql("SELECT * FROM csv_data_tb", engine)
        return df
    except Exception as e:
        st.error(f"KEIT 사업공고 현황 오라클 DB 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400) 
def fetch_national_business_api():
    api_key = st.secrets.get("NATIONAL_BUSINESS_SURVEY_API_KEY", "")
    if not api_key:
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
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def fetch_mss_tech_cert_api():
    api_key = st.secrets.get("MSS_TECH_CERT_API_KEY", "")
    if not api_key:
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
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def fetch_bizinfo_api():
    try:
        engine = get_oracle_engine()
        df = pd.read_sql("SELECT * FROM bizinfo_tb FETCH FIRST 500 ROWS ONLY", engine)
        
        if df.empty:
            return pd.DataFrame()
            
        # 🚨 [대시보드 빈 화면 해결 코드] 오라클 대문자 컬럼명을 원상 복구
        known_keys = ['pblancId', 'pblancNm', 'reqstEndDe', 'reqstBgnde', 'insttNm', 'bizId', 'entrprsStle', 'jrsdcAsct', 'exntcInsttNm', 'pblancUrl']
        mapping = {key.upper(): key for key in known_keys}
        df = df.rename(columns=lambda x: mapping.get(x.upper(), x))
        
        # 기존 마감일 필터 로직
        if 'reqstEndDe' in df.columns:
            df['마감일_계산용'] = pd.to_datetime(df['reqstEndDe'], errors='coerce')
            today = pd.Timestamp(datetime.now().date())
            valid_df = df[(df['마감일_계산용'] >= today) | (df['마감일_계산용'].isna())]
            return valid_df.drop(columns=['마감일_계산용']).head(200).reset_index(drop=True)
        return df.head(200)
            
    except Exception as e:
        st.error(f"오라클 DB(기업마당) 읽기 실패: {e}")
        return pd.DataFrame()
