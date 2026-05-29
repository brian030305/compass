import streamlit as st
import oracledb
import pandas as pd
import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import text

# LOB 데이터(긴 텍스트) 끊김 방지 설정
oracledb.defaults.fetch_lobs = False

# 1. 읽기 전용 엔진 (오라클 다이렉트 - 대문자 컬럼명 유지)
def get_oracle_engine():
    return oracledb.connect(
        user=st.secrets["ORACLE_USER"],
        password=st.secrets["ORACLE_PASSWORD"],
        dsn=st.secrets["ORACLE_DSN"]
    )

# 2. 쓰기(저장) 전용 엔진 (판다스 to_sql 에러 방지용)
def get_sqlalchemy_engine():
    def creator():
        return get_oracle_engine()
    return create_engine("oracle+oracledb://", creator=creator)

def fetch_safety_cert_data():
    url = "https://api.odcloud.kr/api/15040703/v1/uddi:9bbbc4ab-d825-401f-b7c2-ff065808acec"
    headers = {'Authorization': f'Infuser {st.secrets["SAFETY_API_KEY"]}'}
    params = {'page': '1', 'perPage': '100'} 
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            df = pd.DataFrame(response.json()['data'])
            return df.rename(columns={'제품명': '사업/공고/제품명', '제조사명': '관련기관/제조사'})
    except Exception:
        pass
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
    except Exception:
        pass
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
    except Exception:
        pass
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
    except Exception:
        pass
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
    except Exception:
        pass
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
    except Exception:
        pass
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
        return pd.DataFrame()

@st.cache_data(ttl=86400) 
def fetch_national_business_api():
    api_key = st.secrets.get("NATIONAL_BUSINESS_SURVEY_API_KEY", "")
    if not api_key: return pd.DataFrame()
        
    url = "https://api.odcloud.kr/api/15087673/v1/uddi:32e6d6f0-6d01-4f62-b76e-b0ae5b840573" 
    headers = {'Authorization': f'Infuser {api_key}'}
    params = {'page': '1', 'perPage': '1000'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data: return pd.DataFrame(data['data'])
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=86400)
def fetch_mss_tech_cert_api():
    api_key = st.secrets.get("MSS_TECH_CERT_API_KEY", "")
    if not api_key: return pd.DataFrame()
        
    url = "https://api.odcloud.kr/api/3033913/v1/uddi:27bb6889-e56d-4cdc-a222-9f02900c81e7" 
    headers = {'Authorization': f'Infuser {api_key}'}
    params = {'page': '1', 'perPage': '500'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data: return pd.DataFrame(data['data'])
    except Exception:
        pass
    return pd.DataFrame()

def fetch_bizinfo_api():
    try:
        engine = get_oracle_engine()
        df = pd.read_sql("SELECT * FROM bizinfo_tb FETCH FIRST 500 ROWS ONLY", engine)
        
        if df.empty: return pd.DataFrame()
            
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


def admin_fetch_all_users():
    """관리자용: 전체 회원 목록 조회 (대문자 강제 유지)"""
    try:
        engine = get_oracle_engine() # 읽기 전용 엔진
        df = pd.read_sql("SELECT ID, COMPANY, LOCATION, INDUSTRY, TECH FROM users_tb", engine).fillna("")
        df.columns = df.columns.str.upper() # 대문자 통일
        return df
    except Exception as e:
        st.error(f"회원 목록을 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()

def admin_delete_user(user_id):
    """관리자용: 특정 회원 계정 삭제 (CLOB 타입 호환 반영)"""
    try:
        engine = get_sqlalchemy_engine() # 쓰기(저장) 전용 알케미 엔진
        with engine.connect() as conn:
            # TO_CHAR(ID)를 사용하여 CLOB 타입 비교 에러(ORA-00932) 원천 차단
            query = text("DELETE FROM users_tb WHERE TO_CHAR(ID) = :user_id")
            conn.execute(query, {"user_id": str(user_id)})
            conn.commit() # 오라클 필수 커밋
        return True
    except Exception as e:
        st.error(f"계정 삭제 중 오류 발생: {e}")
        return False

def admin_change_user_password(user_id, hashed_pw):
    """관리자용: 특정 회원 비밀번호 강제 변경"""
    try:
        engine = get_sqlalchemy_engine()
        with engine.connect() as conn:
            # UPDATE 문을 사용하여 해당 ID의 비밀번호만 교체합니다.
            query = text("UPDATE users_tb SET PW = :pw WHERE TO_CHAR(ID) = :user_id")
            conn.execute(query, {"pw": hashed_pw, "user_id": str(user_id)})
            conn.commit() 
        return True
    except Exception as e:
        print(f"관리자 비밀번호 변경 오류: {e}")
        return False

def fetch_kstartup_data():
    """K-Startup 창업지원사업 API (웹 화면 직접 출력 디버깅 모드)"""
    url = "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"
    
    # st.secrets에서 키 불러오기
    service_key = st.secrets["KSTARTUP_API_KEY"]
    
    params = {
        'serviceKey': service_key,
        'pageNo': 1,
        'numOfRows': 100,
        'returnType': 'JSON'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        # 🚨 [디버깅 1] HTTP 상태 코드가 200(정상)이 아닐 경우 화면에 에러 원문 띄우기
        if response.status_code != 200:
            st.error(f"⚠️ K-Startup 서버 접근 실패 (코드: {response.status_code})")
            st.code(response.text) # 에러 원문을 화면에 출력
            return pd.DataFrame()
            
        # 🚨 [디버깅 2] 서버 응답이 JSON이 아닐 경우(보통 공공데이터 포털 키 인증 에러 시 발생) 화면에 띄우기
        try:
            result = response.json()
        except Exception as e:
            st.error("⚠️ K-Startup API가 정상적인 JSON 데이터가 아닌 에러 메시지를 보냈습니다.")
            st.info("아래의 서버 응답 원문을 확인해 주세요. (인증키 미등록, 트래픽 초과 등)")
            st.code(response.text[:1000]) 
            return pd.DataFrame()
            
        # 정상적으로 JSON 변환이 되었다면 데이터 추출 시작
        items = []
        if "response" in result and "body" in result["response"] and "items" in result["response"]["body"]:
            items_data = result["response"]["body"]["items"]
            if isinstance(items_data, dict) and "item" in items_data:
                items = items_data["item"]
            elif isinstance(items_data, list):
                items = items_data
        elif "data" in result:
            items = result["data"]
            
        if items:
            df = pd.DataFrame(items)
            
            rename_dict = {}
            if 'postsnNm' in df.columns: rename_dict['postsnNm'] = '사업명'
            elif 'pbancNm' in df.columns: rename_dict['pbancNm'] = '사업명'
            elif 'title' in df.columns: rename_dict['title'] = '사업명'
            
            if 'bizPrchDprtNm' in df.columns: rename_dict['bizPrchDprtNm'] = '소관기관'
            elif 'pancInsttNm' in df.columns: rename_dict['pancInsttNm'] = '소관기관'
            
            if 'rcptBgngDt' in df.columns: rename_dict['rcptBgngDt'] = '접수시작일'
            elif 'pbancRcptBgngDt' in df.columns: rename_dict['pbancRcptBgngDt'] = '접수시작일'
            
            if 'rcptEndDt' in df.columns: rename_dict['rcptEndDt'] = '마감일'
            elif 'pbancRcptEndDt' in df.columns: rename_dict['pbancRcptEndDt'] = '마감일'
            
            if 'dtlPgUrl' in df.columns: rename_dict['dtlPgUrl'] = '상세링크'
            elif 'pblancUrl' in df.columns: rename_dict['pblancUrl'] = '상세링크'
            
            if rename_dict:
                df = df.rename(columns=rename_dict)
                
            return df
            
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"⚠️ K-Startup 파이썬 실행 에러: {str(e)}")
        return pd.DataFrame()
