import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# --- 1. 系統環境配置 ---
CURRENT_APP_VERSION = "3.5.0 (Full-Database-Search)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. AI 引擎配置 (全域檢索模式) ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    genai.configure(api_key=api_key)
    
    # 啟用搜尋工具，確保能搜尋「所有藥品」
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        tools=[{"google_search_retrieval": {}}],
        system_instruction=(
            "你是一位資深台灣臨床藥師，負責搜尋台灣健保署 (NHI) 與食藥署 (TFDA) 資料庫。\n"
            "當使用者輸入藥品名稱或代碼時，你必須精準找出該藥品資訊並依照以下結構輸出：\n\n"
            "1. 【藥品基本資料】：成分、商品名、健保代碼與單價。\n"
            "2. 【臨床適應症與用法】：TFDA 核准用途、建議劑量。\n"
            "3. 【健保給付規定】：是否有特殊規定 (如特定科別、檢驗報告)。\n"
            "4. 【藥師臨床提示】：重大副作用、交互作用、配製注意事項。\n\n"
            "格式要求：嚴禁使用粗體 (**)，使用條列式呈現。禁止提及任何私人公司名稱。"
        )
    )
    return model

if "model" not in st.session_state:
    st.session_state.model = init_gemini()

# --- 3. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>台灣全藥品臨床檢索系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

# 搜尋框：支援全藥品輸入
query = st.text_input("輸入藥品關鍵字", placeholder="例如: SHECO, CEFIN, 或是任何藥品名稱", label_visibility="collapsed")

if query:
    query = query.strip()
    with st.spinner(f"正在連線 NHI/TFDA 資料庫搜尋 '{query}'..."):
        # 建立重試機制解決 429 流量問題
        success = False
        retries = 3
        
        while retries > 0 and not success:
            try:
                # 執行全域搜尋
                response = st.session_state.model.generate_content(f"請搜尋台灣藥品 '{query}' 並製作臨床報告。")
                result_text = response.text.replace('**', '')
                
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0; color: white;">
                    <h3 style="margin: 0;">💊 藥事綜合報告：{query}</h3>
                </div>
                <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                </div>
                """, unsafe_allow_html=True)
                success = True
                
            except Exception as e:
                if "429" in str(e):
                    retries -= 1
                    if retries > 0:
                        st.warning(f"⚠️ 伺服器繁忙，正在進行第 {3-retries} 次自動重試...")
                        time.sleep(5) # 強制等待 5 秒避開限制
                    else:
                        st.error("❌ 搜尋請求過於頻繁，請稍候 30 秒再試。")
                else:
                    st.error(f"❌ 發生錯誤：{e}")
                    break

st.divider()
st.caption("數據來源：經由 AI 即時連線台灣官方健保與食藥署資料庫。")
