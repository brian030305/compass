import streamlit as st
import requests
import pandas as pd

# ★핵심 수정: 모든 함수가 헤더(Header) 방식으로 키를 전달하도록 변경★

def fetch_safety_cert_data():
    url = "https://api.odcloud.kr/api/15040703/v1/uddi:9bbbc4ab-d825-401f-b7c2-ff065808acec"
    # Authorization 헤더에 키를 넣습니다.
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