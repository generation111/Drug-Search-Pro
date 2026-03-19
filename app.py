import streamlit as st
import google.generativeai as genai
import time
import base64
from datetime import datetime

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.5.9 (SDK-Fix)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Streamlit Secrets 設定。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 建立工具清單：使用正確的工具宣告語法
    # 修正：google_search 必須透過此方式宣告
    tools = [{"google_search_retrieval": {}}]

    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', # 建議使用穩定版本
        tools=tools,
        system_instruction=(
            "你是一位極度嚴謹的台灣臨床藥師，專門處理藥品辨識與給付規範。\n"
            "【核心原則】：\n"
            "1. 僅提供 100% 確定的資訊。嚴禁使用發音相似的藥品（如 Cefazolin）進行模擬或舉例。\n"
            "2. 處理歧義：若商品名對應多種成分（例如 CEFIN），必須分別列出對照表，明確區分成分（如 Cephradine 與 Ceftriaxone）及其臨床差異。\n"
            "3. 內容結構：必須包含【健保代碼】、【規格單價】、【穩定性與配製建議】及【臨床適應症】。\n"
            "4. 格式：禁止使用粗體語法 (**)，請用分段與條列式呈現專業感。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面與搜尋邏輯 ---
st.markdown("<h1 style='text-align: center;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>專業藥事管理系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    with st.spinner(f"正在交叉比對台灣健保品項與仿單數據..."):
        try:
            # 傳送搜尋請求
            prompt = f"請查詢台灣健保藥品 '{query}'。若有多個不同成分品項，請務必『分別敘明』其健保代碼、價格及臨床配製上的穩定性差異（例如室溫與冷藏保存時間）。"
            
            response = model.generate_content(prompt)
            result_text = response.text.replace('**', '')

            # 渲染結果
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                <h3 style="margin: 0;">💊 臨床藥事分析：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">DATABASE GROUNDING ACTIVE</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"系統診斷錯誤：{e}")
            st.info("提示：請確保您的 API Key 具備 Search 權限，或嘗試重新整理頁面。")

st.divider()
st.caption(f"穩定版本: {CURRENT_APP_VERSION} | 數據來源：TFDA & NHI Administration")
