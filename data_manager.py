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

# ==========================================
# 📊 [유지] KEIT 사업공고 현황 (유일한 로컬 CSV)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_local_keit_announcement():
    """한국산업기술기획평가원_사업공고 현황 데이터 로드"""
    try:
        return pd.read_csv("한국산업기술기획평가원_사업공고 현황.csv", encoding="cp949", encoding_errors="ignore")
    except Exception:
        try:
            return pd.read_csv("한국산업기술기획평가원_사업공고 현황.csv", encoding="utf-8-sig", encoding_errors="ignore")
        except Exception as e:
            st.error(f"KEIT 사업공고 현황 로드 실패: {e}")
            return pd.DataFrame()

# ==========================================
# 🌐 [신규 전환] 통계청 전국사업체조사 API
# ==========================================
@st.cache_data(ttl=86400) # 통계 데이터이므로 하루(86400초) 단위로 캐시
def fetch_national_business_api():
    """전국사업체조사 공공데이터 API 로드"""
    api_key = st.secrets.get("NATIONAL_BUSINESS_SURVEY_API_KEY", "")
    if not api_key:
        st.warning("전국사업체조사 API 키가 설정되지 않았습니다.")
        return pd.DataFrame()
        
    # 🎯 찾아내신 2023년 최신 URL 적용 완료
    url = "https://api.odcloud.kr/api/15087673/v1/uddi:32e6d6f0-6d01-4f62-b76e-b0ae5b840573" 
    
    # 🚨 [핵심 수정] params가 아닌 headers에 인증키를 넣고, 파라미터명도 odcloud 규격에 맞춥니다.
    headers = {'Authorization': f'Infuser {api_key}'}
    params = {'page': '1', 'perPage': '1000'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # 🚨 [핵심 수정] odcloud API는 'data' 키 안에 곧바로 배열을 줍니다.
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
# 🌐 [신규 전환] 중소벤처기업부 기술개발제품 인증현황 API
# ==========================================
@st.cache_data(ttl=86400)
def fetch_mss_tech_cert_api():
    """기술개발제품 인증현황 공공데이터 API 로드"""
    api_key = st.secrets.get("MSS_TECH_CERT_API_KEY", "")
    if not api_key:
        st.warning("기술개발제품 인증현황 API 키가 설정되지 않았습니다.")
        return pd.DataFrame()
        
    # 🎯 찾아내신 2023년 최신 URL 적용 완료
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
# 🌐 기업마당 (Bizinfo) API 로드 함수 (안전 파싱 적용)
# ==========================================
@st.cache_data(ttl=1800) 
def fetch_bizinfo_api():
    api_key = st.secrets.get("BIZINFO_API_KEY", "")
    
    if not api_key:
        st.warning("기업마당 API 키가 secrets 파일에 설정되지 않았습니다.")
        return pd.DataFrame()
        
    url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
    
    params = {
        "crtfcKey": api_key,
        "dataType": "json",  
        "searchCnt": "500"   
    }
    
    try:
        # 🚨 [핵심 수정] 봇(Bot) 차단 필터링을 우회하기 위한 가짜 브라우저 헤더 세팅
        custom_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # headers와 verify=False(SSL 인증서 검사 무시) 파라미터 추가
        response = requests.get(url, params=params, headers=custom_headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # --- 🎯 [핵심 수정] 어떤 형태의 데이터가 오든 유연하게 꺼내는 로직 ---
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # 정상적인 데이터인 경우
                if 'jsonArray' in data:
                    items = data['jsonArray']
                elif 'item' in data:
                    items = data['item']
                # 에러 메시지이거나 알 수 없는 구조인 경우
                else:
                    st.error(f"🚨 API가 데이터를 거절했습니다. 기업마당 응답 내용: {data}")
                    st.info("💡 팁: 기업마당 홈페이지에 등록된 IP 주소와 현재 PC의 IP 주소가 일치하는지 확인하세요.")
                    return pd.DataFrame()
            
            if not items:
                return pd.DataFrame()
                
            df = pd.DataFrame(items)
            
            # --- 마감일 필터링 로직 ---
            if 'reqstEndDe' in df.columns:
                df['마감일_계산용'] = pd.to_datetime(df['reqstEndDe'], errors='coerce')
                today = pd.Timestamp(datetime.now().date())
                valid_df = df[(df['마감일_계산용'] >= today) | (df['마감일_계산용'].isna())]
                valid_df = valid_df.drop(columns=['마감일_계산용']).head(200).reset_index(drop=True)
                return valid_df
            else:
                return df.head(200)
                
        else:
            st.error(f"기업마당 API 서버 통신 에러: HTTP {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"기업마당 데이터 통신 실패: {e}")
        return pd.DataFrame()