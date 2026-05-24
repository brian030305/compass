# python -m streamlit run app.py
import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import re
from docx import Document
from datetime import datetime, timedelta
from data_manager import (
    fetch_safety_cert_data, fetch_mss_data, fetch_ktl_data,
    fetch_kiat_data, fetch_keit_min_data, fetch_keit_rd_data
)

# 1. 기본 설정
st.set_page_config(page_title="창업나침반 - Startup Compass", layout="wide")

st.markdown(
    """
    <div style="background-color:#0e243a; padding:15px; border-radius:10px; margin-bottom:25px;">
        <h2 style="color:white; margin:0; display:inline-block;">🧭 창업나침반 <span style="font-size:16px; font-weight:normal; color:#b0c4de;">Startup Compass</span></h2>
    </div>
    """, 
    unsafe_allow_html=True
)

if 'current_page' not in st.session_state:
    st.session_state.current_page = st.query_params.get("page", "대시보드")

def change_page(page_name):
    st.session_state.current_page = page_name
    st.query_params["page"] = page_name

# --- AI 스마트 분류 함수 ---
@st.cache_data(ttl=3600) 
def get_ai_classified_data():
    df = get_ai_classified_data()
    if df.empty: return df
    
    classification_prompt = """
    다음 지원사업 공고 제목을 읽고, 아래 5개 업종 중 가장 적합한 하나를 선택해. 
    답변은 딱 업종명만 출력할 것.
    업종 리스트: ['IT/소프트웨어', '제조업', '바이오/헬스케어', '에너지/환경', '기타']
    공고명: {title}
    """
    
    categories = []
    progress_bar = st.progress(0)
    for i, (_, row) in enumerate(df.iterrows()):
        title = str(row.get('사업명', '')) 
        response = st.session_state.chat_session.send_message(classification_prompt.format(title=title))
        categories.append(response.text.strip())
        progress_bar.progress((i + 1) / len(df))
    
    df['업종태그'] = categories
    progress_bar.empty()
    return df

# 2. 사이드바 메뉴
with st.sidebar:
    st.markdown("### 🛠️ 메뉴")
    st.button("📊 대시보드", use_container_width=True, type="primary" if st.session_state.current_page == '대시보드' else "secondary", on_click=change_page, args=('대시보드',))
    st.button("💬 AI 어시스턴트", use_container_width=True, type="primary" if st.session_state.current_page == 'AI 어시스턴트' else "secondary", on_click=change_page, args=('AI 어시스턴트',))
    st.button("✨ AI 매칭", use_container_width=True, type="primary" if st.session_state.current_page == 'AI 매칭' else "secondary", on_click=change_page, args=('AI 매칭',))
    st.button("📈 생존율 예측", use_container_width=True, type="primary" if st.session_state.current_page == '생존율 예측' else "secondary", on_click=change_page, args=('생존율 예측',))
    st.button("📅 지원 캘린더", use_container_width=True, type="primary" if st.session_state.current_page == '지원 캘린더' else "secondary", on_click=change_page, args=('지원 캘린더',))
    st.button("📄 보고서 생성", use_container_width=True, type="primary" if st.session_state.current_page == '보고서 생성' else "secondary", on_click=change_page, args=('보고서 생성',))
    
    st.divider()
    st.markdown("### 📋 기업 정보 설정")
    
    default_company = st.query_params.get("company", "테크스타트업(주)")
    default_industry = st.query_params.get("industry", "선택해주세요")
    default_tech = st.query_params.get("tech", "")
    
    company_input = st.text_input("기업명", value=default_company)
    
    industry_options = ["선택해주세요", "IT/소프트웨어", "제조업", "바이오/헬스케어", "에너지/환경", "기타"]
    ind_index = industry_options.index(default_industry) if default_industry in industry_options else 0
    industry_input = st.selectbox("어떤 업종에 속하시나요?", industry_options, index=ind_index)
    
    tech_field_input = st.text_input("필요한 기술 분야 키워드", value=default_tech, placeholder="예: 드론, 인공지능")
    
    if st.button("정보 저장 및 연동", use_container_width=True):
        st.session_state.company_name = company_input
        st.session_state.industry = industry_input
        st.session_state.tech_field = tech_field_input
        st.session_state.dashboard_metrics = None 
        
        st.query_params["company"] = company_input
        st.query_params["industry"] = industry_input
        st.query_params["tech"] = tech_field_input
        
        st.session_state.survival_report = None
        if "chat_session" in st.session_state:
            del st.session_state.chat_session
        st.success("기업 정보가 연동되었습니다!")
        st.rerun()

# 3. AI 및 데이터 처리 로직 (캐싱 적용)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def search_safety_cert(): return fetch_safety_cert_data().to_string() if not fetch_safety_cert_data().empty else "데이터 없음"
def search_mss_support(): return fetch_mss_data().to_string() if not fetch_mss_data().empty else "데이터 없음"
def search_ktl_test(): return fetch_ktl_data().to_string() if not fetch_ktl_data().empty else "데이터 없음"
def search_kiat_worldclass(): return fetch_kiat_data().to_string() if not fetch_kiat_data().empty else "데이터 없음"
def search_keit_ministry(): return fetch_keit_min_data().to_string() if not fetch_keit_min_data().empty else "데이터 없음"
def search_keit_rnd(): return fetch_keit_rd_data().to_string() if not fetch_keit_rd_data().empty else "데이터 없음"

tools_list = [search_safety_cert, search_mss_support, search_ktl_test, search_kiat_worldclass, search_keit_ministry, search_keit_rnd]

@st.cache_data(ttl=600)
def get_ai_classified_data():
    df_mss = fetch_mss_data()
    df_rd = fetch_keit_rd_data()
    valid_dfs = [d for d in [df_mss, df_rd] if not d.empty]
    return pd.concat(valid_dfs, ignore_index=True) if valid_dfs else pd.DataFrame()

base_instruction = "당신은 한국의 스타트업과 중소기업을 돕는 최고 수준의 AI 컨설턴트입니다."
if "industry" in st.session_state and "tech_field" in st.session_state:
    if st.session_state.industry != "선택해주세요" or st.session_state.tech_field:
        base_instruction += f"\n\n[고객 정보]\n- 업종: {st.session_state.industry}\n- 기술 분야: {st.session_state.tech_field}\n★이 기업 정보를 기준으로 사업을 필터링하세요."

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", tools=tools_list, system_instruction=base_instruction)
    st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)

# 4. 메인 화면 출력부
company_name = st.session_state.get('company_name', st.query_params.get("company", "테크스타트업(주)"))
ind_str = st.session_state.get('industry', st.query_params.get("industry", "선택해주세요"))
tech_str = st.session_state.get('tech_field', st.query_params.get("tech", ""))


# ------- 대시보드 설정 -----------
if st.session_state.current_page == '대시보드':
    if 'show_chatbot' not in st.session_state:
        st.session_state.show_chatbot = False

    header_col1, header_col2 = st.columns([8, 2])
    with header_col1:
        st.header(f"안녕하세요, {company_name}")
        st.caption(f"💡 {ind_str} · 핵심 기술: {tech_str if tech_str else '미설정'}")
    with header_col2:
        if st.button("💬 AI 챗봇 켜기/끄기", use_container_width=True):
            st.session_state.show_chatbot = not st.session_state.show_chatbot
            st.rerun()
            
    if st.session_state.show_chatbot:
        main_col, ai_col = st.columns([7, 3], gap="large") 
    else:
        main_col, ai_col = st.columns([1, 0.01]) 

    with main_col:
        # [핵심] 기업 정보 설정 여부 판단
        is_info_set = (ind_str != "선택해주세요" and ind_str != "")
        
        if is_info_set:
            # --- [기능 1] 마감 임박 공지 (데일리 리포트 배너) ---
            df = get_ai_classified_data()
            urgent_count = 0
            
            if not df.empty:
                industry_keywords = {
                    "IT/소프트웨어": ["IT", "소프트웨어", "SW", "정보통신", "플랫폼", "앱", "데이터", "인공지능", "AI"],
                    "제조업": ["제조", "생산", "설비", "부품", "소재", "하드웨어", "공장", "가공"],
                    "바이오/헬스케어": ["바이오", "의료", "헬스", "건강", "의약", "생명", "제약", "병원"],
                    "에너지/환경": ["에너지", "환경", "녹색", "친환경", "탄소", "수소", "재생", "에코"],
                    "기타": []
                }
                if ind_str in industry_keywords:
                    keywords = industry_keywords[ind_str]
                    if keywords:
                        pattern = '|'.join(keywords)
                        df = df[df.apply(lambda row: row.astype(str).str.contains(pattern, case=False).any(), axis=1)]
                if tech_str:
                    df = df[df.apply(lambda row: row.astype(str).str.contains(tech_str, case=False).any(), axis=1)]
                
                today = datetime.now().date()
                for _, row in df.iterrows():
                    row_string = " ".join([str(val) for val in row.values if pd.notna(val)])
                    dates = re.findall(r'20\d{2}[-./]\d{2}[-./]\d{2}', row_string)
                    if dates:
                        end_date_str = sorted([d.replace('.', '-').replace('/', '-') for d in dates])[-1]
                        try:
                            end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                            days_left = (end_date_obj - today).days
                            if 0 <= days_left <= 7: 
                                urgent_count += 1
                        except ValueError:
                            pass
            
            if urgent_count > 0:
                st.error(f"🚨 **주목!** 귀사에 적합한 지원사업 중 마감이 **7일 이내로 임박한 공고가 {urgent_count}건** 있습니다. 캘린더 탭에서 서둘러 확인해 보세요!")
            elif not df.empty and len(df) > 0:
                st.info(f"💡 오늘 기준 **{ind_str}** 분야에 지원 가능한 새로운 맞춤형 공고가 **{len(df)}건** 대기 중입니다.")
            else:
                st.info("💡 조건에 맞는 지원사업이 없습니다.")

            st.divider()
            
            # --- [기능 2] 대시보드 핵심 지표 요약표 ---
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            match_count = len(df) if not df.empty else 0
            
            total_fund = match_count * 0.8  
            survival_rate = min(95, 65 + (match_count * 0.5))
            
            with kpi1:
                st.metric(label="매칭된 지원사업", value=f"{match_count}개", delta="신청 가능")
            with kpi2:
                st.metric(label="예상 생존율", value=f"{survival_rate:.1f}%", delta="데이터 기반")
            with kpi3:
                st.metric(label="이번 달 마감", value=f"{urgent_count}건", delta="신청 임박", delta_color="inverse")
            with kpi4:
                st.metric(label="총 지원 가능 금액", value=f"{total_fund:.1f}억원", delta="추정치")
                
            st.divider()
            
            # --- [기능 3] 생존율 리스크 시각화 바 ---
            if 'last_ind_str' not in st.session_state:
                st.session_state.last_ind_str = ind_str
            
            if st.session_state.last_ind_str != ind_str:
                st.session_state.dashboard_metrics = None
                st.session_state.last_ind_str = ind_str
                st.rerun()

            if st.session_state.get('dashboard_metrics') is None:
                with st.spinner("AI가 공고 데이터를 바탕으로 점수를 정밀 계산 중입니다..."):
                    data_summary = df.head(10).to_string() if not df.empty else ""
                    analysis_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
                    analysis_prompt = f"""
                    업종: {ind_str}, 기술: {tech_str}
                    매칭된 공고 데이터 요약: {data_summary}
                    이 데이터를 바탕으로 재무안정성, 기술경쟁력, 시장성장성, 팀역량을 0~100점으로 평가해줘.
                    반드시 숫자 4개만 콤마로 구분해서 줄 것. 예: 75,82,60,88
                    """
                    res = analysis_model.generate_content(analysis_prompt)
                    found_numbers = re.findall(r'\d+', res.text)
                    
                    if len(found_numbers) >= 4:
                        st.session_state.dashboard_metrics = [int(n) for n in found_numbers[:4]]
                    else:
                        st.error("분석 실패: AI가 유효한 점수를 반환하지 못했습니다.")
                        st.stop()

            if st.session_state.dashboard_metrics:
                s1, s2, s3, s4 = st.session_state.dashboard_metrics
                risk_col1, risk_col2 = st.columns(2)
                with risk_col1:
                    st.markdown("**재무 안정성**")
                    st.progress(s1, text=f"{s1}%")
                    st.markdown("**시장 성장성**")
                    st.progress(s3, text=f"{s3}%")
                    
                with risk_col2:
                    st.markdown("**기술 경쟁력**")
                    st.progress(s2, text=f"{s2}%")
                    st.markdown("**팀 역량**")
                    st.progress(s4, text=f"{s4}%")
                    
        else:
            # 정보 설정 전 심플한 안내
            st.info("💡 좌측 사이드바에서 기업 정보를 설정하시면 맞춤형 지원사업 알림과 생존율 진단을 받아보실 수 있습니다.")

    # --- [기능 4] 우측 AI 챗봇 토글 영역 ---
    if st.session_state.show_chatbot:
        with ai_col:
            st.markdown("### 🟢 AI 어시스턴트")
            
            chat_container = st.container(height=550)
            with chat_container:
                for message in st.session_state.chat_session.history:
                    role = "user" if message.role == "user" else "assistant"
                    with st.chat_message(role):
                        st.markdown(message.parts[0].text)
            
            user_input = st.chat_input("질문하거나 지시를 내려보세요...", key="dashboard_chat_input")
            
            if user_input:
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(user_input)
                    
                    with st.chat_message("assistant"):
                        with st.spinner("AI가 분석 중..."):
                            response = st.session_state.chat_session.send_message(user_input)
                            st.markdown(response.text)
                st.rerun()

# ------- AI 어시스턴트 설정 -----------
elif st.session_state.current_page == 'AI 어시스턴트':
    st.header("💬 AI 어시스턴트")
    for message in st.session_state.chat_session.history:
        if message.role == "user" or (message.role == "model" and message.parts[0].text):
            with st.chat_message(message.role):
                st.markdown(message.parts[0].text)
    user_input = st.chat_input("궁금한 공공데이터를 물어보세요!")
    if user_input:
        with st.chat_message("user"): st.markdown(user_input)
        with st.chat_message("model"):
            with st.spinner("AI가 데이터를 분석 중입니다..."):             
                response = st.session_state.chat_session.send_message(user_input, stream=True)                         
                st.write_stream(response)
        st.rerun()

# ------- AI 매칭 설정 -----------
elif st.session_state.current_page == 'AI 매칭':
    st.subheader("✨ AI 맞춤형 지원사업 매칭")
    st.caption(f"현재 매칭 조건 ➔ 업종: **{ind_str}** | 기술 키워드: **{tech_str if tech_str else '미설정'}**")
    
    if st.button("공고 리스트 불러오기"):
        df = get_ai_classified_data()
        
        if df.empty:
            st.warning("불러올 수 있는 공고 데이터가 존재하지 않습니다.")
        else:
            industry_keywords = {
                "IT/소프트웨어": ["IT", "소프트웨어", "SW", "정보통신", "플랫폼", "앱", "데이터", "인공지능", "AI"],
                "제조업": ["제조", "생산", "설비", "부품", "소재", "하드웨어", "공장", "가공"],
                "바이오/헬스케어": ["바이오", "의료", "헬스", "건강", "의약", "생명", "제약", "병원"],
                "에너지/환경": ["에너지", "환경", "녹색", "친환경", "탄소", "수소", "재생", "에코"],
                "기타": []
            }
            
            if ind_str != "선택해주세요" and ind_str in industry_keywords:
                keywords = industry_keywords[ind_str]
                if keywords:
                    pattern = '|'.join(keywords)
                    ind_mask = df.apply(lambda row: row.astype(str).str.contains(pattern, case=False).any(), axis=1)
                    df = df[ind_mask]
            
            if tech_str:
                tech_mask = df.apply(lambda row: row.astype(str).str.contains(tech_str, case=False).any(), axis=1)
                df = df[tech_mask]
            
            if df.empty:
                st.info("선택하신 업종 및 기술 키워드와 매칭되는 실시간 공고가 없습니다. 조건을 변경해 보세요.")
            else:
                st.session_state.filtered_df = df  
            st.success(f"조건에 맞는 공고를 총 {len(df)}건 찾았습니다!")
            st.dataframe(df, use_container_width=True)

# ------- 생존율 예측 설정 -----------
elif st.session_state.current_page == '생존율 예측':
    st.subheader("📈 산업군 기반 생존율 정밀 진단")
    if 'survival_report' not in st.session_state:
        st.session_state.survival_report = None
        
    if st.button("생존율 정밀 분석 시작"):
        if ind_str == "선택해주세요":
            st.warning("왼쪽 사이드바에서 정보를 먼저 설정해주세요!")
        else:
            with st.spinner("기업 데이터를 분석 중입니다..."):
                prompt = f"""
                현재 대상 기업은 '{ind_str}' 업종이며, '{tech_str}' 기술을 다루고 있습니다.
                이 기업을 위한 '생존율 정밀 진단 리포트'를 반드시 아래 4가지 목차에 맞춰서 전문적으로 작성해 줘.

                1. 산업군 생존 환경 분석 (현재 시장 트렌드)
                2. 주요 리스크 요인 3가지 (기술, 자금, 시장 측면)
                3. 리스크 극복 및 생존율 향상 전략
                4. 추천 정부지원사업 및 활용 방안 (검색된 데이터 기반)
                """
                response = st.session_state.chat_session.send_message(prompt)
                st.session_state.survival_report = response.text
                
    if st.session_state.survival_report:
        st.markdown(st.session_state.survival_report)

# ------- 지원 캘린터 설정 -----------
elif st.session_state.current_page == '지원 캘린더':
    from streamlit_calendar import calendar
    
    st.subheader("📅 맞춤형 지원사업 마감 일정")
    st.caption(f"현재 반영된 조건 ➔ 업종: **{ind_str}** | 기술 키워드: **{tech_str if tech_str else '미설정'}**")
    
    df = get_ai_classified_data()
    
    if df.empty:
        st.warning("일정을 표시할 공고 데이터가 존재하지 않습니다.")
    else:
        industry_keywords = {
            "IT/소프트웨어": ["IT", "소프트웨어", "SW", "정보통신", "플랫폼", "앱", "데이터", "인공지능", "AI"],
            "제조업": ["제조", "생산", "설비", "부품", "소재", "하드웨어", "공장", "가공"],
            "바이오/헬스케어": ["바이오", "의료", "헬스", "건강", "의약", "생명", "제약", "병원"],
            "에너지/환경": ["에너지", "환경", "녹색", "친환경", "탄소", "수소", "재생", "에코"],
            "기타": []
        }
        
        if ind_str != "선택해주세요" and ind_str in industry_keywords:
            keywords = industry_keywords[ind_str]
            if keywords:
                pattern = '|'.join(keywords)
                df = df[df.apply(lambda row: row.astype(str).str.contains(pattern, case=False).any(), axis=1)]
        
        if tech_str:
            df = df[df.apply(lambda row: row.astype(str).str.contains(tech_str, case=False).any(), axis=1)]
        
        st.markdown("---")
        st.markdown("**📅 보고 싶은 달로 이동하기**")
        
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 3])
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        with nav_col1:
            target_year = st.selectbox("연도", range(2020, 2031), index=range(2020, 2031).index(current_year), label_visibility="collapsed")
        with nav_col2:
            target_month = st.selectbox("월", range(1, 13), index=current_month - 1, label_visibility="collapsed")
            
        target_date_str = f"{target_year}-{target_month:02d}-01"
        
        events = []
        list_data = [] 
        cols = df.columns.tolist()
        
        for _, row in df.iterrows():
            row_values = [str(val) for val in row.values if pd.notna(val)]
            row_string = " ".join(row_values)
            
            dates = re.findall(r'20\d{2}[-./]\d{2}[-./]\d{2}', row_string)
            dates = [d.replace('.', '-').replace('/', '-') for d in dates]
            dates = sorted(list(set(dates))) 
            
            if not dates: continue 
                
            start_date_str = dates[0]
            end_date_str = dates[-1] if len(dates) > 1 else dates[0]
            
            title_col = next((c for c in cols if any(k in c for k in ['사업명', '공고명', '과제명', '제목', '명'])), cols[0])
            full_title = str(row[title_col])
            display_title = full_title[:30] + "..." if len(full_title) > 30 else full_title
            
            url_match = re.search(r'(https?://[^\s]+)', row_string)
            event_url = url_match.group(1) if url_match else ""
            
            events.append({
                "title": display_title,
                "start": start_date_str,
                "end": (datetime.strptime(end_date_str, "%Y-%m-%d").date() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "backgroundColor": "#0e243a" if event_url else "#7f8c8d", 
                "borderColor": "#0e243a" if event_url else "#7f8c8d"
            })
            
            list_data.append({
                "사업명": full_title,
                "마감일": end_date_str,
                "상세링크": event_url if event_url else None
            })
        
        if events:
            calendar(events=events, options={
                "locale": "ko",
                "initialDate": target_date_str,
                "initialView": "dayGridMonth",
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
                "displayEventTime": False
            })
            
            st.markdown("---")
            st.subheader("🔗 지원사업 바로가기 링크 명단")
            st.caption("아래 표에서 원하시는 공고의 **'🔗 바로가기'** 링크를 클릭하시면 보안 차단 없이 새 창에서 열립니다.")
            
            list_df = pd.DataFrame(list_data)
            
            st.dataframe(
                list_df,
                use_container_width=True,
                column_config={
                    "사업명": st.column_config.TextColumn("사업명", width="large"),
                    "마감일": st.column_config.TextColumn("마감일", width="small"),
                    "상세링크": st.column_config.LinkColumn("상세링크", display_text="🔗 바로가기", width="medium")
                },
                hide_index=True
            )
        else:
            st.warning("현재 설정하신 조건으로 신청 가능한 기간 내의 공고가 없습니다.")

# ------- 보고서 생성 설정 -----------
elif st.session_state.current_page == '보고서 생성':
    st.subheader("📄 AI 자동 생성 보고서 보관함")
    
    if 'filtered_df' in st.session_state and st.session_state.filtered_df is not None:
        df = st.session_state.filtered_df
    else:
        df = get_ai_classified_data()
    
    if df.empty:
        st.warning("현재 연동된 공고 데이터가 없습니다. 먼저 매칭 탭에서 데이터를 확인해주세요.")
    else:
        cols = df.columns.tolist()
        title_col = next((c for c in cols if any(k in c for k in ['사업명', '공고명', '과제명', '제목', '명'])), cols[0])
        project_list = [str(x) for x in df[title_col].dropna().unique() if str(x).strip()]
        
        selected_business = st.selectbox(
            "작성할 지원사업명을 검색하거나 선택하세요:",
            options=["직접 입력할게요 (선택)"] + project_list
        )
        
        if selected_business == "직접 입력할게요 (선택)":
            target_business = st.text_input("지원사업명을 직접 입력해주세요:")
        else:
            target_business = selected_business
            
        if st.button("사업계획서 초안 생성", type="primary"):
            if not target_business: 
                st.warning("사업명을 입력하거나 선택해주세요.")
            else:
                with st.spinner(f"'{target_business}' 사업계획서 작성 중..."):
                    prompt = f"""
                    사업명: '{target_business}'
                    우리 기업 업종: {ind_str}
                    핵심 기술: {tech_str}
                    
                    위 정보를 바탕으로 해당 지원사업에 제출할 사업계획서 초안을 작성해 줘.
                    반드시 아래 4가지 목차를 포함하여 심사위원들을 설득할 수 있는 논리적이고 전문적인 문장으로 작성할 것.
                    
                    1. 창업 동기 및 필요성
                    2. 기술 차별성 및 우수성
                    3. 시장 진입 및 확대 전략
                    4. 향후 추진 일정
                    """
                    response = st.session_state.chat_session.send_message(prompt)
                    st.session_state.report_content = response.text
                    st.session_state.current_target_business = target_business
                    
    if "report_content" in st.session_state and "current_target_business" in st.session_state:
        st.markdown(st.session_state.report_content)
        
        clean_text = st.session_state.report_content
        clean_text = re.sub(r'\*+', '', clean_text)  
        clean_text = re.sub(r'#+\s*', '', clean_text) 
        clean_text = re.sub(r'`+', '', clean_text)    
        
        doc = Document()
        doc.add_heading(f"{st.session_state.current_target_business} 사업계획서", 0)
        doc.add_paragraph(clean_text)
        
        bio = io.BytesIO()
        doc.save(bio)
        
        st.divider()
        st.download_button(
            label="📥 기호 없이 깔끔한 워드(.docx) 다운로드", 
            data=bio.getvalue(), 
            file_name=f"{st.session_state.current_target_business}_사업계획서.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )