import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# --- 1. 初始化 ---
def init_services():
    client = None
    if "openai" in st.secrets:
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    return client

client = init_services()

# --- 2. 健保 API 檢索函數 ---
def search_nhi_drug(drug_name):
    # 健保署資料開放平台 API 介接網址
    api_url = f"https://info.nhi.gov.tw/api/iode0010/v1/rest/datastore/A21030000I-E41001-001"
    params = {
        "limit": 10,
        "offset": 0,
        "q": drug_name  # 關鍵字搜尋：藥品名稱或代碼
    }
    try:
        response = requests.get(api_url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get('result', {}).get('records', [])
    except:
        return []
    return []

# --- 3. UI 介面 ---
st.set_page_config(page_title="藥速知 MedQuick (健保同步版)", layout="wide")
st.title("💊 藥速知 MedQuick")
st.caption("連線衛福部健保用藥資料開放平台")

query = st.text_input("輸入藥品名稱 (例如: CHEF, CEFAZOLIN, HOLISOON)", placeholder="搜尋...")

if query:
    target = query.strip().upper()
    
    with st.spinner('正在同步健保資料庫與臨床數據...'):
        # 第一步：從健保 API 取得官方資訊
        nhi_records = search_nhi_drug(target)
        
        if nhi_records:
            st.success(f"找到 {len(nhi_records)} 筆健保登記資料")
            with st.expander("查看健保登記明細"):
                st.table(pd.DataFrame(nhi_records))
            
            # 準備提供給 AI 的背景資訊
            nhi_context = f"健保官方資料顯示：{nhi_records[0]}"
        else:
            st.warning("健保開放資料庫中查無此精確名稱，將進行廣域臨床檢索。")
            nhi_context = "查無健保開放資料記錄。"

        # 第二步：調用 AI 進行深度臨床分析
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一位藥學專家。請根據健保資料與全球藥典，提供精確的學名、適應症、用法用量及禁忌。嚴禁錯誤關聯。"},
                    {"role": "user", "content": f"藥品：{target}。參考背景：{nhi_context}"}
                ],
                temperature=0
            )
            st.markdown(f"### 📋 臨床分析報告\n{response.choices[0].message.content}")
        except Exception as e:
            st.error(f"AI 檢索失敗: {e}")
