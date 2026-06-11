import os
import sys
import base64
import zipfile
import requests
import pandas as pd
from sqlalchemy import create_engine
import oracledb
from bs4 import BeautifulSoup  # 3.5단계를 위한 라이브러리 추가
import time                    # 3.5단계를 위한 라이브러리 추가

print("🚀 [시스템 시작] 새로운 final_bot 가동 시작...")

oracle_user = os.getenv("ORACLE_USER")
oracle_password = os.getenv("ORACLE_PASSWORD")
oracle_dsn = os.getenv("ORACLE_DSN")
wallet_password = os.getenv("WALLET_PASSWORD")
wallet_base64 = os.getenv("WALLET_BASE64")
bizinfo_key = os.getenv("BIZINFO_API_KEY")

if not all([oracle_user, oracle_password, oracle_dsn, wallet_password, wallet_base64, bizinfo_key]):
    print("❌ 에러: 깃허브 Secrets 설정 중 누락된 항목이 존재합니다.")
    sys.exit(1)

print("2️⃣ 보안 지갑 파일(Wallet) 가상 가동 중...")
os.makedirs("./bot_wallet", exist_ok=True)
try:
    with open("bot_wallet.zip", "wb") as f:
        f.write(base64.b64decode(wallet_base64))
    with zipfile.ZipFile("bot_wallet.zip", 'r') as zip_ref:
        zip_ref.extractall("./bot_wallet")
    print("✔️ 지갑 복원 완료")
except Exception as e:
    print(f"❌ 지갑 파일 복원 실패: {e}")
    sys.exit(1)

print("3️⃣ 기업마당 공식 API 서버 호출 중...")
url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
params = {
    'crtfcKey': bizinfo_key,
    'dataType': 'json',
    'searchCnt': '300'
}

# 🚨 중기부 방화벽 차단을 뚫기 위한 일반 브라우저 위장 헤더
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(f"📡 API 서버 응답 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        raw_text = response.text.strip()
        print(f"🔍 원본 데이터 앞글자 샘플: {raw_text[:150]}")
        
        try:
            json_res = response.json()
        except Exception as json_err:
            print(f"❌ 에러: API 응답을 JSON으로 변환 실패: {json_err}")
            sys.exit(1)
            
        if isinstance(json_res, list):
            api_data = json_res
        elif isinstance(json_res, dict) and 'jsonArray' in json_res:
            api_data = json_res['jsonArray']
        elif isinstance(json_res, dict) and 'data' in json_res:
            api_data = json_res['data']
        else:
            api_data = [json_res] if json_res else []

        if not api_data:
            print("⚠️ 경고: 수집된 공고 배열이 비어 있습니다.")
            sys.exit(1)
            
        biz_df = pd.DataFrame(api_data).fillna("")
        print(f"✔️ 데이터프레임 변환 성공! 컬럼 목록: {list(biz_df.columns)}")
    else:
        print(f"❌ API 호출 실패 (HTTP 상태 코드: {response.status_code})")
        print(f"💡 서버 에러 내용: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"❌ API 통신 실패 단계 에러: {e}")
    sys.exit(1)

# =====================================================================
# 🚀 3.5️⃣ 기업마당 상세 페이지 크롤링 및 AI 심층 검증 (원본 훼손 없이 추가)
# =====================================================================
print("3.5️⃣ 기업마당 상세 페이지 크롤링 및 AI 심층 검증 시작...")

school_api_key = os.getenv("SCHOOL_API_KEY")
biz_df['ai_pass_yn'] = "미검증"
biz_df['ai_summary'] = "대기중"

TARGET_LIMIT = 10 

for idx, row in biz_df.head(TARGET_LIMIT).iterrows():
    pblanc_url = str(row.get('pblancUrl', ''))
    title = str(row.get('pblancNm', ''))
    
    if not pblanc_url.startswith("http"):
        continue
        
    print(f"🔍 [{idx+1}/{TARGET_LIMIT}] 원문 독해 및 AI 검증 중: {title[:15]}...")
    
    try:
        page_res = requests.get(pblanc_url, headers=headers, timeout=20)
        soup = BeautifulSoup(page_res.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.extract()
            
        core_text = soup.get_text(separator=' ', strip=True)[:3000]
        
        if school_api_key:
            ai_prompt = f"""
            당신은 정부지원사업 심사역입니다. 다음은 공고문 상세 원문입니다.
            문서를 꼼꼼히 읽고 일반적인 스타트업이 지원하기에 까다로운 '제한 조건'이나 '독소 조항'이 있으면 '불가(X)', 지원이 무난하면 '가능(O)'으로 첫 문장에 명시한 뒤 3줄로 이유를 요약하세요.
            [원문 데이터]: {core_text}
            """
            
            school_api_url = "https://factchat-cloud.mindlogic.ai/v1/api/anthropic/messages"
            ai_headers = {
                "Authorization": f"Bearer {school_api_key}",
                "Content-Type": "application/json"
            }
            ai_payload = {
                "model": "claude-sonnet-4-5-20250929",
                "messages": [{"role": "user", "content": ai_prompt}]
            }
            
            ai_res = requests.post(school_api_url, json=ai_payload, headers=ai_headers, timeout=120)
            
            if ai_res.status_code == 200:
                result_data = ai_res.json()
                try: ai_answer = result_data.get('content', [{}])[0].get('text', str(result_data))
                except: ai_answer = str(result_data)
                
                if "X" in ai_answer or "불가" in ai_answer: biz_df.at[idx, 'ai_pass_yn'] = "X"
                else: biz_df.at[idx, 'ai_pass_yn'] = "O"
                    
                biz_df.at[idx, 'ai_summary'] = ai_answer[:200]
            else:
                biz_df.at[idx, 'ai_pass_yn'] = "통신 에러"
                biz_df.at[idx, 'ai_summary'] = f"상태코드: {ai_res.status_code}"
                
        time.sleep(2) 
        
    except Exception as e:
        print(f"❌ 크롤링/AI 에러 발생: {e}")
        biz_df.at[idx, 'ai_pass_yn'] = "에러"
        biz_df.at[idx, 'ai_summary'] = str(e)[:100]

# =====================================================================

print("4️⃣ 오라클 클라우드 DB 최종 적재 시작...")
def get_oracle_connection():
    return oracledb.connect(
        user=oracle_user,
        password=oracle_password,
        dsn=oracle_dsn,
        wallet_location="./bot_wallet",
        wallet_password=wallet_password
    )

try:
    engine = create_engine('oracle+oracledb://', creator=get_oracle_connection)
    biz_df = biz_df.astype(str)
    biz_df.to_sql('bizinfo_tb', engine, if_exists='replace', index=False)
    print("🎉 [대성공] 오라클 DB 자동 업데이트 가동 성공! (AI 데이터 포함)")
except Exception as e:
    print(f"❌ 오라클 DB 적재 에러: {e}")
    sys.exit(1)
