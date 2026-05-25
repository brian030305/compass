import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.title("🔄 기업마당 리얼 데이터 수집기 (내 PC 전용)")
st.info("이 프로그램은 내 PC의 한국 IP를 이용해 기업마당 데이터를 긁어와 구글 시트에 저장합니다.")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_real_data():
    api_key = st.secrets.get("BIZINFO_API_KEY", "")
    url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
    params = {"crtfcKey": api_key, "dataType": "json", "searchCnt": "800"}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, params=params, headers=headers, verify=False, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('jsonArray', data.get('item', [])) if isinstance(data, dict) else data
        df = pd.DataFrame(items)
        return df
    else:
        return pd.DataFrame()

if st.button("🚀 데이터 긁어오기 및 구글 시트에 저장", type="primary"):
    with st.spinner("기업마당에서 최신 공고를 가져와 구글 시트에 업로드하는 중입니다..."):
        df = get_real_data()
        
        if not df.empty:
            # 🎯 방금 만든 BizInfo 탭에 데이터를 통째로 덮어쓰기 합니다.
            conn.update(worksheet="BizInfo", data=df)
            st.success(f"✅ 총 {len(df)}건의 공고가 구글 시트 'BizInfo' 탭에 성공적으로 저장되었습니다! (업데이트 시간: {datetime.now().strftime('%H:%M:%S')})")
        else:
            st.error("데이터를 가져오는 데 실패했습니다.")