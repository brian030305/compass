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

# 3. 기업마당 정식 자체 API 호출 및 데이터 수집
print("3️⃣ 기업마당 공식 API 서버 호출 중...")

# 💡 [핵심 교체] 사용자님이 발급받으신 기업마당 전용 API 주소와 파라미터 양식으로 변경합니다.
url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

bizinfo_key = os.getenv("BIZINFO_API_KEY")
if not bizinfo_key:
    print("❌ 에러: 깃허브 비밀키에서 BIZINFO_API_KEY를 불러오지 못했습니다.")
    sys.exit(1)

# 기업마당 자체 API 필수 규격 파라미터 세팅
params = {
    'crtfcKey': bizinfo_key, # 👈 이미지에 적혀있던 필수 인증키 파라미터명
    'dataType': 'json',      # JSON 데이터 타입 강제 지정
    'searchCnt': '500'       # 한 번에 최대 500건 수집
}

try:
    # 기업마당 서버로 직접 요청을 보냅니다.
    response = requests.get(url, params=params, timeout=30)
    if response.status_code == 200:
        # 기업마당 자체 API는 응답 구조가 공공데이터포털과 다를 수 있으므로 안전하게 파싱합니다.
        try:
            json_res = response.json()
            # 기업마당 응답 데이터 구조에 맞춰 추출 (응답 구조가 리스트 형태이거나 json_res인 경우 대비)
            api_data = json_res if isinstance(json_res, list) else json_res.get('jsonArray', json_res.get('data', []))
        except Exception:
            # 혹시나 예외적인 가공 처리가 필요할 경우를 대비해 데이터프레임으로 우선 변환
            api_data = response.json()
            
        if not api_data:
            print("⚠️ API 호출은 성공했으나 수집된 공고 내용물이 비어 있습니다.")
            sys.exit(1)
            
        biz_df = pd.DataFrame(api_data).fillna("")
        print(f"✔️ 최신 기업마당 자체 공고 {len(biz_df)}건 수집 완료!")
    else:
        print(f"❌ API 호출 실패 (HTTP 상태 코드: {response.status_code})")
        print(f"💡 서버 응답 내용: {response.text}")
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