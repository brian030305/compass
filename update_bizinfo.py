import os
import sys
import base64
import zipfile
import requests
import pandas as pd
from sqlalchemy import create_engine
import oracledb

print("🚀 [시스템 시작] 기업마당 마스터 자동화 봇 가동...")

oracle_user = os.getenv("ORACLE_USER")
oracle_password = os.getenv("ORACLE_PASSWORD")
oracle_dsn = os.getenv("ORACLE_DSN")
wallet_password = os.getenv("WALLET_PASSWORD")
wallet_base64 = os.getenv("WALLET_BASE64")
bizinfo_key = os.getenv("BIZINFO_API_KEY")

if not all([oracle_user, oracle_password, oracle_dsn, wallet_password, wallet_base64, bizinfo_key]):
    print("❌ 에러: 깃허브 Secrets 설정 중 누락된 항목이 존재합니다. 6개 키를 모두 확인하세요.")
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

# 3️⃣ 기업마당 공식 API 서버 호출 중... (한국 프록시 우회 적용)
print("3️⃣ 기업마당 공식 API 서버 호출 중 (국내 IP 우회 가동)...")
url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
params = {
    'crtfcKey': bizinfo_key,
    'dataType': 'json',
    'searchCnt': '300'
}

# 🚨 한국 공용 프록시 서버들을 리스트로 넣어 방화벽을 무력화합니다.
# (무료 한국 프록시 IP 중 하나가 막히더라도 다음 IP가 뚫도록 배열 처리)
proxy_list = [
    {"http": "http://210.114.10.22:80"},
    {"http": "http://112.221.73.194:3128"},
    {"http": "http://221.143.238.106:8080"}
]

response = None
for proxy in proxy_list:
    try:
        print(f"📡 한국 프록시 우회 서버 경유 시도 중: {proxy['http']}")
        response = requests.get(url, params=params, proxies=proxy, timeout=15)
        if response.status_code == 200:
            print("🎯 [우회 성공] 중기부 방화벽을 완벽하게 뚫었습니다!")
            break
    except Exception as proxy_err:
        print(f"⚠️ 해당 프록시 서버 응답 없음, 다음 서버로 전환합니다.")
        continue

# 만약 프록시를 다 돌았는데도 안 되면 최종 예외 처리
if response is None or response.status_code != 200:
    print("❌ 최종 경고: 준비된 국내 프록시 서버가 모두 차단되었거나 응답이 없습니다.")
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
    print(f"❌ 오라클 DB 최종 적재 단계 에러: {e}")
    sys.exit(1)
