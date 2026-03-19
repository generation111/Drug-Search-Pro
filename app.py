import streamlit as st
import google.generativeai as genai
import time
import base64
from datetime import datetime

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.5.8 (Ambiguity-Check)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 嚴格設定：不確定就不要回答，禁止模糊類比
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=(
            "你是一位嚴謹的台灣臨床藥師。回覆規則如下：\n"
            "1. 僅根據 TFDA、健保署 (NHI) 與藥廠官方仿單進行回覆。\n"
            "2. 若查詢詞對應到多種不同成分（如 CEFIN 對應到 Cephradine 與 Ceftriaxone），必須『分別敘明』其臨床差異，禁止混淆。\n"
            "3. 禁止模糊推論。若資料庫查無確切對應之台灣核准藥品，請直接回答『查無此藥品資訊』，嚴禁使用相似發音藥品（如 Cefazolin）進行舉例。\n"
            "4. 輸出必須包含：【健保代碼】、【成分分類】、【臨床用途差異】與【配製保存要求】。\n"
            "5. 禁止使用粗體語法 (**)。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面與搜尋 ---
st.markdown("<h1 style='text-align: center;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>同名異分自動偵測版 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    with st.spinner(f"正在交叉比對健保資料庫與仿單..."):
        try:
            # 傳送搜尋請求，要求區分同名異分藥品
            prompt = f"請檢索商品名 '{query}'。若有多個成分（如 Cephradine 或 Ceftriaxone），請生成對照表單分別說明其健保代碼、價格、適應症與穩定性差異。"
            response = model.generate_content(prompt, tools=[{'google_search': {}}])
            result_text = response.text.replace('**', '')

            # 顯示對照介面
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                <h3 style="margin: 0;">🔍 搜尋結果：{query}</h3>
                <p style="font-size: 12px; color: #94a3b8; margin-top: 5px;">已啟動臨床歧義偵測邏輯</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"查詢中斷：{e}")

st.divider()
st.caption(f"穩定版本: {CURRENT_APP_VERSION} | 資料來源：TFDA & NHI")
