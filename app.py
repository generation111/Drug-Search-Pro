import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime

# --- 系統配置 ---
APP_VERSION = "1.3.5"
st.set_page_config(page_title="臨床藥事快搜 Pro", layout="wide")

# API 配置 (建議之後改用 Secrets 管理)
API_KEY = "您的_GEMINI_API_KEY" 
genai.configure(api_key=API_KEY)

# --- 介面美化 ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #1E3A8A; margin-bottom: 0; }
    .rx-tag { background: #2563EB; color: white; padding: 2px 10px; border-radius: 5px; font-style: italic; }
    .report-container { background: white; padding: 30px; border-radius: 15px; shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# --- 功能邏輯 ---
def fetch_med_info(drug_name):
    model = genai.GenerativeModel("gemini-1.5-flash") # 建議用 flash 速度最快
    prompt = f"你是資深臨床藥師。請針對藥品『{drug_name}』進行極速分析：1. 適應症 2. 標準用法 3. 關鍵禁忌與警告。請分段清晰，使用中標題，禁用粗體語法。"
    response = model.generate_content(prompt)
    return response.text

# --- UI 佈局 ---
st.markdown(f'<h1 class="main-header"><span class="rx-tag">Rx</span> Clinical Pro</h1>', unsafe_allow_html=True)
st.caption(f"專業藥事情報系統 | 版本代號：{APP_VERSION}")

query = st.text_input("🔍 請輸入藥品名稱 (學名或商品名)：", placeholder="例如: Holisoon, Pregabalin...")

if query:
    with st.status("正在檢索臨床數據...", expanded=True) as status:
        st.write("連線至醫學資料庫...")
        result_text = fetch_med_info(query)
        st.write("完成分析。")
        status.update(label="搜尋完成！", state="complete", expanded=False)
    
    # 顯示結果
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📋 {query} 臨床報告")
        st.markdown(f'<div class="report-container">{result_text}</div>', unsafe_allow_html=True)
    
    with col2:
        st.info("💡 提示：本報告僅供專業醫療人員參考，臨床決策請依據實際仿單。")
        # 下載按鈕
        st.download_button(
            label="📥 下載 HTML 報告",
            data=f"<html><body>{result_text}</body></html>",
            file_name=f"{query}_report.html",
            mime="text/html"
        )