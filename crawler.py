# streamlit run crawler.py
import requests
import pandas as pd
import streamlit as st

# secrets.toml에 적어둔 변수명으로 안전하게 키 가져오기
biz_key = st.secrets["BIZINFO_API_KEY"]

def test_crawl():
    print("API 호출 시작...")
    
    url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
    params = {
        "crtfcKey": biz_key,
        "dataType": "json"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # 기업마당 API 응답 구조에 맞게 실제 데이터 리스트만 빼오기 위한 처리
        if isinstance(data, dict):
            # 딕셔너리 형태라면 어떤 '키'들을 보내줬는지 터미널에 먼저 출력해 봅니다.
            print("💡 API 응답 데이터 키 목록:", data.keys())
            
            # 보통 기업마당은 'jsonArray'라는 이름으로 리스트를 줍니다.
            if 'jsonArray' in data:
                api_data = data['jsonArray']
            else:
                # 만약 다른 이름이라면 일단 빈 리스트를 넣고, 터미널 출력을 보고 파악합니다.
                api_data = [] 
        elif isinstance(data, list):
            # 데이터가 처음부터 리스트 형태라면 그대로 사용합니다.
            api_data = data
        else:
            api_data = []
            
        # 대시보드에 띄울 핵심 컬럼만 추출
        parsed_list = []
        for item in api_data:
            parsed_list.append({
                "공고명": item.get('pblancNm', '제목 없음'),
                "주관기관": item.get('jrsdInsttNm', ''),
                "접수기간": item.get('reqstBeginEndDe', ''),
                "상세링크": item.get('pblancUrl', '')
            })
            
        # 판다스 데이터프레임으로 변환하여 표 형태로 터미널에 출력
        if parsed_list:
            df = pd.DataFrame(parsed_list)
            print("\n🎉 데이터 전처리 성공! 추출된 표(DataFrame) 상위 5개 결과:")
            print(df.head())
        else:
            print("\n⚠️ 전처리할 데이터 리스트를 찾지 못했습니다. 위의 '키 목록'을 확인해 주세요.")
            
    else:
        print("접속 실패! 상태 코드:", response.status_code)

if __name__ == "__main__":
    test_crawl()