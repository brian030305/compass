import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET

def fetch_public_data(api_key):
    # 공공데이터포털 중소기업 지원사업 조회 API URL
    url = "https://apis.data.go.kr/B552735/mss/getMssSupport"
    params = {
        'serviceKey': api_key, # 인증키
        'numOfRows': '10',     # 한 번에 10개만 테스트로 가져오기
        'pageNo': '1'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        # XML 형태의 응답을 파싱
        root = ET.fromstring(response.content)
        data = []
        # 각 항목별로 데이터 추출
        for item in root.findall('.//item'):
            data.append({
                '사업명': item.find('pblancNm').text if item.find('pblancNm') is not None else '',
                '소관기관': item.find('juridicalOrgNm').text if item.find('juridicalOrgNm') is not None else '',
                '마감일': item.find('reqstEndDe').text if item.find('reqstEndDe') is not None else ''
            })
        return pd.DataFrame(data)
    else:
        return None

st.title("📡 실시간 공공데이터 API 테스트")
api_key_input = st.text_input("발급받은 일반 인증키(Encoding)를 입력하세요", type="password")

if st.button("실시간 공고 가져오기"):
    if api_key_input:
        df = fetch_public_data(api_key_input)
        if df is not None:
            st.success("데이터를 실시간으로 성공적으로 긁어왔습니다!")
            st.dataframe(df)
        else:
            st.error("데이터 가져오기 실패 (인증키를 확인하세요)")
    else:
        st.warning("인증키를 입력해 주세요.")

# python -m streamlit run api_test.py        