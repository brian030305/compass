import os
import sys
import base64
import zipfile
import requests
import pandas as pd
from sqlalchemy import create_engine
import oracledb
from bs4 import BeautifulSoup
import time

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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=90)
    print(f"📡 API 서버 응답 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        json_res = response.json()
        if isinstance(json_res, list): api_data = json_res
        elif isinstance(json_res, dict) and 'jsonArray' in json_res: api_data = json_res['jsonArray']
        elif isinstance(json_res, dict) and 'data' in json_res: api_data = json_res['data']
        else: api_data = [json_res] if json_res else []

        if not api_data:
            print("⚠️ 경고: 수집된 공고 배열이 비어 있습니다.")
            sys.exit(1)
            
        biz_df = pd.DataFrame(api_data).fillna("")
        print(f"✔️ 데이터프레임 변환 성공! 수집 데이터: {len(biz_df)}건")
    else:
        print(f"❌ API 호출 실패 (HTTP 상태 코드: {response.status_code})")
        sys.exit(1)
except Exception as e:
    print(f"❌ API 통신 실패 단계 에러: {e}")
    sys.exit(1)

# 🚀 [추가된 로직] 기존 DB를 확인하여 AI 검증을 패스할 '신규 공고'만 골라냅니다.

print("3.1️⃣ 오라클 DB에서 과거 AI 분석 기록 불러오기...")

def get_oracle_connection():
    return oracledb.connect(
        user=oracle_user, password=oracle_password, dsn=oracle_dsn,
        wallet_location="./bot_wallet", wallet_password=wallet_password
    )

engine = create_engine('oracle+oracledb://', creator=get_oracle_connection)

biz_df['ai_pass_yn'] = "미검증"
biz_df['ai_summary'] = "대기중"
biz_df['ai_region'] = "전국"
biz_df['ai_keyword'] = "일반"

new_records_idx = [] # 새로 AI를 돌려야 할 공고의 위치값 모음

try:
    existing_df = pd.read_sql("SELECT pblancId, ai_pass_yn, ai_summary, ai_region, ai_keyword FROM bizinfo_tb", engine)
    existing_dict = existing_df.set_index('pblancId').to_dict('index')

    for idx, row in biz_df.iterrows():
        pid = str(row.get('pblancId', ''))
        # DB에 이미 기록이 있고, 분석이 끝난 상태라면 과거 데이터를 덮어씌움
        if pid in existing_dict and existing_dict[pid]['ai_summary'] != "대기중":
            biz_df.at[idx, 'ai_pass_yn'] = existing_dict[pid]['ai_pass_yn']
            biz_df.at[idx, 'ai_summary'] = existing_dict[pid]['ai_summary']
            biz_df.at[idx, 'ai_region'] = existing_dict[pid]['ai_region']
            biz_df.at[idx, 'ai_keyword'] = existing_dict[pid]['ai_keyword']
        else:
            new_records_idx.append(idx)
    print(f"✔️ 기존 데이터 매핑 완료! (순수 신규 분석 대상: {len(new_records_idx)}건)")
except Exception as e:
    print(f"⚠️ 기존 DB 테이블이 없거나 읽을 수 없습니다. (최초 실행으로 간주): {e}")
    new_records_idx = biz_df.index.tolist()



# 🚀 3.5️⃣ 기업마당 상세 페이지 크롤링 및 AI 심층 검증 (기존 로직 유지)

print("3.5️⃣ 기업마당 상세 페이지 크롤링 및 AI 통합 분석 시작...")

school_api_key = os.getenv("SCHOOL_API_KEY")

TARGET_LIMIT = 20 # 💡 하루에 새로 들어오는 공고 처리량 한도 (API 비용 방어)
process_count = 0

# 💡 전체를 돌지 않고, 새로 골라낸 신규 데이터(new_records_idx)만 순회합니다.
for idx in new_records_idx:
    if process_count >= TARGET_LIMIT:
        print(f"⚠️ 일일 AI 분석량({TARGET_LIMIT}건)에 도달하여 중단합니다. (나머지는 내일 분석)")
        break

    row = biz_df.loc[idx]
    pblanc_url = str(row.get('pblancUrl', ''))
    title = str(row.get('pblancNm', ''))
    
    if not pblanc_url.startswith("http"):
        continue
        
    print(f"🔍 [신규 {process_count+1}/{len(new_records_idx)}] AI 분석 중: {title[:15]}...")
    
    try:
        page_res = requests.get(pblanc_url, headers=headers, timeout=20)
        soup = BeautifulSoup(page_res.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.extract()
            
        core_text = soup.get_text(separator=' ', strip=True)[:3000]
        
        if school_api_key:
            ai_prompt = f"""
            당신은 정부지원사업 심사역입니다. 다음은 공고문 상세 원문입니다.
            문서를 꼼꼼히 읽고 반드시 아래 4가지 항목을 양식에 맞춰 출력하세요. 부연 설명은 절대 금지합니다.

            [양식]
            판정: (제한조건이나 독소조항이 많아 스타트업 지원이 불가하면 X, 무난하면 O)
            요약: (판정의 이유를 3줄로 요약)
            지역: (서울, 부산, 전국 등. 해당 없으면 '전국')
            키워드: (IT, SW, 제조업, 청년 등 핵심 키워드 최대 3개, 쉼표로 구분)

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
                
                pass_yn, summary, region, keyword = "O", "요약 실패", "전국", "일반"
                for line in ai_answer.split('\n'):
                    line = line.strip()
                    if line.startswith("판정:"): pass_yn = "X" if "X" in line else "O"
                    elif line.startswith("요약:"): summary = line.replace("요약:", "").strip()
                    elif line.startswith("지역:"): region = line.replace("지역:", "").strip()
                    elif line.startswith("키워드:"): keyword = line.replace("키워드:", "").strip()
                
                biz_df.at[idx, 'ai_pass_yn'] = pass_yn
                biz_df.at[idx, 'ai_summary'] = summary[:200]
                biz_df.at[idx, 'ai_region'] = region
                biz_df.at[idx, 'ai_keyword'] = keyword
            else:
                biz_df.at[idx, 'ai_pass_yn'] = "통신 에러"
                biz_df.at[idx, 'ai_summary'] = f"상태코드: {ai_res.status_code}"
                
        time.sleep(2) 
        process_count += 1
        
    except Exception as e:
        print(f"❌ 크롤링/AI 에러 발생: {e}")
        biz_df.at[idx, 'ai_pass_yn'] = "에러"
        biz_df.at[idx, 'ai_summary'] = str(e)[:100]

# =====================================================================

print("4️⃣ 오라클 클라우드 DB 최종 적재 시작...")
try:
    biz_df = biz_df.astype(str)
    # 기존 데이터와 신규 데이터가 병합된 완성본이 DB에 한 번에 덮어씌워집니다.
    biz_df.to_sql('bizinfo_tb', engine, if_exists='replace', index=False)
    print("🎉 [대성공] 오라클 DB 자동 업데이트 가동 성공! (과거 데이터 보존 + 신규 AI 태그 추가)")
except Exception as e:
    print(f"❌ 오라클 DB 적재 에러: {e}")
    sys.exit(1)
