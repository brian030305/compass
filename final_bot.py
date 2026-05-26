import os
import sys
import base64
import zipfile
import requests
import pandas as pd
from sqlalchemy import create_engine
import oracledb

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
    print("🎉 [대성공] 오라클 DB 자동 업데이트 가동 성공!")
except Exception as e:
    print(f"❌ 오라클 DB 적재 에러: {e}")
    sys.exit(1)
