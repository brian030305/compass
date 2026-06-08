import requests
import streamlit as st

def call_school_llm(prompt, model_type="gemini", system_prompt=None):
    """
    학교 통합 플랫폼을 통해 AI를 호출하는 단일 라우터 함수입니다.
    model_type에 "gemini" 또는 "claude"를 입력하여 목적지를 변경합니다.
    """
    
    # 1. 안전 금고에서 단일 API 키 꺼내기
    try:
        api_key = st.secrets["SCHOOL_API_KEY"]
    except KeyError:
        return "⚠️ 오류: .streamlit/secrets.toml 파일에 SCHOOL_API_KEY가 없습니다."

    base_url = "https://factchat-cloud.mindlogic.ai/v1/api"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 2. 목적지(URL) 및 데이터 포장(JSON) 규격 분기
    if model_type == "claude":
        url = f"{base_url}/anthropic/messages"
        # 최고 성능의 클로드 모델 지정
        payload = {
            "model": "claude-opus-4-5-20251101",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        }
        if system_prompt:
            payload["system"] = system_prompt

    elif model_type == "gemini":
        url = f"{base_url}/google/models/generate-content"
        # 가볍고 빠른 제미나이 모델 지정
        payload = {
            "model": "gemini-2.5-flash",
            "contents": [{"parts": [{"text": prompt}]}]
        }
        # 구글 규격의 시스템 프롬프트 (필요시)
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}
            
    else:
        return "⚠️ 오류: 지원하지 않는 model_type 입니다."

    # 3. 학교 서버로 통신 발사
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # HTTP 에러 발생 시 예외 처리로 던짐
        result_data = response.json()

        # 4. 제조사별로 다른 응답 포장지 뜯기
        if model_type == "claude":
            return result_data["content"][0]["text"]
        elif model_type == "gemini":
            return result_data["candidates"][0]["content"]["parts"][0]["text"]
            
    except Exception as e:
        error_msg = f"API 호출 오류: {e}"
        if 'response' in locals() and response.text:
            error_msg += f"\n상세 내용: {response.text}"
        return error_msg
