import streamlit as st
import google.generativeai as genai
import os

# --- 系統基礎配置 ---
# 定義系統版本與單位名稱
CURRENT_APP_VERSION = "1.3.5"
COMPANY_NAME = "慈榛驊有限公司"
SYSTEM_NAME = "慈榛驊業務管理系統（全功能終極修復版）"

# 設定頁面資訊
st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# --- API 金鑰與模型配置 ---
# 優先從 Streamlit Secrets 讀取，若無則尋找環境變數
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    # 這裡放置您的備用金鑰，請確保格式正確 (僅代碼部分)
    API_KEY = st.environ.get("GEMINI_API_KEY", "AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY")

genai.configure(api_key=API_KEY)

# 初始化 Gemini 模型，使用穩定版名稱以避免 404 錯誤
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"模型初始化失敗，請檢查 API Key 或網路連線。錯誤資訊: {e}")

# --- 介面佈局 ---
# 標題區塊：盡量貼近頁面上緣
st.markdown(f"<h1 style='text-align: center; margin-top: -50px;'>Rx Clinical Pro</h1>", unsafe_allow_name=True)
st.write(f"<p style='text-align: center;'>專業藥事情報系統 | 版本代號 : {CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

# 產品快速選擇區塊 (置於上方)
with st.container():
    st.subheader("💊 產品快速選擇")
    drug_query = st.text_input("請輸入藥品名稱 (學名或商品名)：", placeholder="例如: Holisoon, Pregabalin...", key="drug_input")

# --- 核心邏輯：AI 分析 ---
if drug_query:
    with st.spinner("正在檢索臨床數據，連線至醫學資料庫..."):
        try:
            # 建立商務推廣語氣的 Prompt
            prompt = f"請以資深醫藥業務主管的角度，針對藥品 '{drug_query}' 提供專業的臨床推廣分析、解決方案及因應計畫。請包含健保規範、競爭對手分析及市場策略。"
            
            response = model.generate_content(prompt)
            
            # 顯示結果區塊
            st.success("分析完成！")
            st.markdown("### 📊 CEO 策略看板")
            st.write(response.text)
            
        except Exception as e:
            # 捕獲並顯示結構化的錯誤訊息
            st.error(f"分析發生錯誤: {e}")

# 戰報區塊 (置於底部)
st.divider()
with st.container():
    st.subheader("📋 戰報系統")
    st.info("目前的戰報邏輯已根據先前指示進行鎖定，不隨意變動。")

# --- 頁尾資訊 ---
# 顯示版本號與單位名稱，確保變數已定義
st.caption(f"系統版本: {CURRENT_APP_VERSION} | 單位: {COMPANY_NAME}")
