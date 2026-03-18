import streamlit as st
import google.generativeai as genai
import os

# --- 1. 系統基礎配置 ---
# 移除 COMPANY_NAME 與 SYSTEM_NAME 變數
CURRENT_APP_VERSION = "1.3.5"

# 設定頁面資訊 (標題改為通用專業名稱)
st.set_page_config(page_title="Rx Clinical Pro", layout="wide")

# --- 2. API 金鑰與模型配置 ---
# 優先從 Streamlit Secrets 讀取，確保雲端部署正常
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    # 本地測試備用 (請確保此為單行字串，不含 curl 或多餘引號)
    API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY")

genai.configure(api_key=API_KEY)

# 初始化 Gemini 1.5 Flash 穩定版
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"模型初始化失敗，請檢查 API 配置。錯誤: {e}")

# --- 3. 介面佈局 (保持簡潔專業) ---
# 標題區塊：使用正確的參數 unsafe_allow_html
st.markdown(f"<h1 style='text-align: center; margin-top: -50px;'>Rx Clinical Pro</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>專業藥事情報系統 | 版本代號 : {CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

# 搜尋區塊
st.subheader("💊 藥品臨床數據檢索")
drug_query = st.text_input("請輸入藥品名稱 (學名或商品名)：", placeholder="例如: Holisoon, Pregabalin...", key="drug_input")

# --- 4. 核心邏輯：AI 醫藥分析 ---
if drug_query:
    with st.spinner("正在連線至醫學資料庫進行分析..."):
        try:
            # 建立符合資深醫藥主管觀點的指令
            prompt = (
                f"你現在是一位資深醫藥業務主管。請針對藥品 '{drug_query}' "
                f"提供專業的推廣分析、健保規範說明、競爭對手差異化分析，"
                f"並針對開發醫療院所提出具體的解決方案與應對計畫。"
            )
            
            response = model.generate_content(prompt)
            
            # 顯示結果
            st.success("分析完成！")
            with st.expander("📊 查看 CEO 策略看板分析結果", expanded=True):
                st.write(response.text)
                
        except Exception as e:
            # 捕獲並顯示結構化錯誤，便於排錯
            st.error(f"分析發生錯誤: {e}")

# --- 5. 頁尾資訊 ---
st.divider()
# 僅顯示版本號，移除公司名稱資訊
st.caption(f"系統版本: {CURRENT_APP_VERSION}")
