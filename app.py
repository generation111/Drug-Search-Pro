import streamlit as st
import google.generativeai as genai
import sys

# --- 1. 系統初始化 ---
APP_VERSION = "1.3.5"
SYSTEM_NAME = "慈榛驊業務管理系統（全功能終極修復版）"
st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# API 配置 - 確保金鑰完全乾淨
GEMINI_API_KEY = "AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY".strip()

# --- 2. 介面美化 ---
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 1rem !important; }}
    .main-header {{ font-size: 2.2rem; font-weight: 800; color: #1E3A8A; }}
    .error-box {{ padding: 20px; background-color: #FEE2E2; border-radius: 10px; border: 1px solid #EF4444; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. 診斷功能：檢查環境是否正常 ---
def check_environment():
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return True, "環境就緒"
    except Exception as e:
        return False, str(e)

# --- 4. 畫面佈局 ---
st.markdown(f'<div class="main-header">🧬 {SYSTEM_NAME}</div>', unsafe_allow_html=True)
st.caption(f"版本代號：{APP_VERSION} | 開發單位：慈榛驊有限公司")

# 啟動時先做一次自我診斷
is_ok, msg = check_environment()
if not is_ok:
    st.error(f"系統核心啟動失敗：{msg}")
    st.info("請檢查您的網路連線，或確認 Python 環境中 google-generativeai 套件是否安裝正確。")

query = st.text_input("🔍 藥品臨床數據查詢：", placeholder="例如: Holisoon, Pregabalin...")

if query:
    # 建立一個佔位符，確保結果能被刷新出來
    container = st.container()
    
    try:
        with st.spinner(f"正在連線至醫學資料庫分析 {query}..."):
            model = genai.GenerativeModel("gemini-1.5-flash")
            # 依照業務管理系統要求的專業語氣
            prompt = f"您是資深醫藥主管。請針對『{query}』提供：1.適應症 2.用法 3.禁忌。禁用粗體，分段清晰。"
            
            # 關鍵：加入 stream=True 確保內容是逐字產出，避免長久等待
            response = model.generate_content(prompt, stream=True)
            
            full_response = ""
            with container:
                st.markdown("---")
                st.subheader(f"📋 {query} 臨床摘要報告")
                res_area = st.empty() # 建立動態文字區
                
                for chunk in response:
                    full_response += chunk.text
                    res_area.markdown(f"```\n{full_response}\n```") # 用 Code block 格式確保文字必出
                    
    except Exception as e:
        st.markdown(f'<div class="error-box"><b>分析中斷：</b><br>{str(e)}</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("© 2026 慈榛驊有限公司")
