import os
import sys
import base64
import zipfile
import requests
import pandas as pd
from sqlalchemy import create_engine
import oracledb

print("🚀 깃허브 자동화 봇: 기업마당 최신 데이터 수집 및 오라클 DB 업데이트를 시작합니다...")

# 1. 깃허브 비밀키(Secrets) 환경변수 로드 및 검증
oracle_user = os.getenv("ORACLE_USER")
oracle_password = os.getenv("ORACLE_PASSWORD")
oracle_dsn = os.getenv("ORACLE_DSN")
wallet_password = os.getenv("WALLET_PASSWORD")
wallet_base64 = os.getenv("WALLET_BASE64")

if not all([oracle_user, oracle_password, oracle_dsn, wallet_password, wallet_base64]):
    print("❌ 에러: 깃허브 비밀키(Secrets) 설정 중 누락된 항목이 있습니다. 5개 키를 모두 확인하세요.")
    sys.exit(1)

# 2. 전달받은 암호문(Base64)을 디코딩하여 전자지갑(Wallet) 폴더 복원
print("2️⃣ 보안 지갑 파일(Wallet) 복원 중...")
os.makedirs("./bot_wallet", exist_ok=True)
try:
    with open("bot_wallet.zip", "wb") as f:
        f.write(base64.b64decode(wallet_base64))

    with zipfile.ZipFile("bot_wallet.zip", 'r') as zip_ref:
        zip_ref.extractall("./bot_wallet")
    print("✔️ 지갑 복원 및 압축 해제 완료")
except Exception as e:
    print(f"❌ 지갑 파일 복원 실패: {e}")
    sys.exit(1)

# 3. 기업마당 공공데이터 API 호출 및 데이터 수집
print("3️⃣ 기업마당 최신 API 데이터 호출 중...")
url = "https://api.odcloud.kr/api/3034791/v1/uddi:80a74cfd-55d2-4dd3-81c7-d01567d0b3c4"
params = {'page': '1', 'perPage': '1000', 'returnType': 'JSON'}

bizinfo_key = os.getenv("BIZINFO_API_KEY")
if not bizinfo_key:
    print("❌ 에러: 깃허브 비밀키에서 BIZINFO_API_KEY를 불러오지 못했습니다.")
    sys.exit(1)

# 💡 [핵심 교체] 공공데이터포털 특유의 인증키 파싱 에러를 방지하기 위해 
# headers 대신 params에 직접 인증키를 심어서 보내는 가장 확실한 방식으로 전환합니다.
params['serviceKey'] = bizinfo_key

try:
    # headers 옵션을 제외하고 params로만 요청을 보냅니다.
    response = requests.get(url, params=params, timeout=30)
    if response.status_code == 200:
        api_data = response.json().get('data', [])
        if not api_data:
            print("⚠️ API 응답에 'data' 내용물이 비어 있습니다. API 키(인코딩/디코딩)를 교체해야 할 수 있습니다.")
            sys.exit(1)
        biz_df = pd.DataFrame(api_data).fillna("")
        print(f"✔️ 최신 기업마당 공고 {len(biz_df)}건 수집 완료!")
    else:
        print(f"❌ API 호출 실패 (HTTP 상태 코드: {response.status_code})")
        print(f"💡 서버 응답 내용: {response.text}") # 👈 에러 원인을 더 자세히 보기 위해 로그 추가
        sys.exit(1)
except Exception as e:
    print(f"❌ API 통신 에러 발생: {e}")
    sys.exit(1)

# 4. 오라클 클라우드 데이터베이스 접속 및 테이블 덮어쓰기
print("4️⃣ 오라클 클라우드 DB 접속 및 'bizinfo_tb' 테이블 업데이트 중...")
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
    # 기존 오라클의 소문자 'bizinfo_tb' 테이블을 수집한 최신 데이터 데이터프레임으로 완전히 갈아끼웁니다.
    biz_df.to_sql('bizinfo_tb', engine, if_exists='replace', index=False)
    print("🎉 [성공] 오라클 DB의 'bizinfo_tb' 테이블이 최신 공고로 완전 자동 업데이트되었습니다!")
except Exception as e:
    print(f"❌ 오라클 DB 데이터 적재 실패: {e}")
    sys.exit(1)