import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- 系統配置 ---
APP_VERSION = "1.3.5"
st.set_page_config(page_title="臨床藥事快搜 Pro", layout="wide")

# API 配置 (加入 .strip() 確保金鑰前後無多餘字元，徹底解決連線錯誤)
GEMINI_API_KEY = "AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY".strip()
genai.configure(api_key=GEMINI_API_KEY)

# --- 介面美化 (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .block-container { padding-top: 1.5rem !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #1E3A8A; margin-bottom: 0; }
    .rx-tag { background: #2563EB; color: white; padding: 2px 10px; border-radius: 5px; font-style: italic; }
    .report-container { 
        background: white; padding: 25px; border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;
        line-height: 1.7; color: #1E293B;
    }
    h2 { color: #2563EB; border-left: 5px solid #2563EB; padding-left: 10px; margin: 20px 0 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 核心分析功能 ---
def fetch_med_info(drug_name):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # 提示詞優化：融入專業藥師與醫學推廣語氣
        prompt = (
            f"您現在是一位資深臨床藥師。請針對藥品『{drug_name}』進行專業、精確的臨床分析。\n\n"
            f"請依照下列結構回應：\n"
            f"## 1. 適應症 (Indications)\n"
            f"## 2. 標準用法 (Dosage & Administration)\n"
            f"## 3. 關鍵禁忌與警告 (Contraindications & Warnings)\n\n"
            f"規範：使用繁體中文，內容分段清晰，禁用粗體(**)語法，並以專業藥事情報風格撰寫。"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 檢索失敗：{str(e)}\n\n請檢查 API Key 狀態或網路連線。"

# --- UI 佈局 ---
st.markdown(f'<h1 class="main-header"><span class="rx-tag">Rx</span> Clinical Pro</h1>', unsafe_allow_html=True)
st.caption(f"專業藥事情報系統 | 版本代號：{APP_VERSION} | 數據支持：Google Gemini")

query = st.text_input("🔍 請輸入藥品名稱 (學名或商品名)：", placeholder="例如: Holisoon, Pregabalin...", key="search_query")

if query:
    with st.status("正在檢索臨床數據...", expanded=True) as status:
        st.write("同步連線至醫學資料庫...")
        result_text = fetch_med_info(query)
        st.write("AI 分析完成。")
        status.update(label="檢索成功！", state="complete", expanded=False)
    
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📋 {query} 臨床摘要報告")
        st.markdown(f'<div class="report-container">{result_text}</div>', unsafe_allow_html=True)
    
    with col2:
        st.info("💡 **專業備註**：\n本報告僅供專業醫療人員參考，臨床決策請務必依據官方最新仿單。")
        
        # 報告下載功能
        today = datetime.now().strftime("%Y%m%d")
        st.download_button(
            label="📥 下載專業報告 (HTML)",
            data=f"<h2>{query} 臨床報告</h2><hr>{result_text}",
            file_name=f"{query}_Report_{today}.html",
            mime="text/html",
            use_container_width=True
        )

# --- 頁尾 ---
st.markdown("---")
st.caption("© 2026 慈榛驊有限公司 | 本系統由 Gemini 1.5 Flash 驅動")
