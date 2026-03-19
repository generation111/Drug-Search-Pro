import streamlit as st
import google.generativeai as genai
import time

# --- 1. 系統環境配置 ---
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心分析引擎 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        tools=[{"google_search_retrieval": {}}],
        system_instruction=(
            "你是一位資深台灣臨床藥師。請針對指定藥品搜尋 TFDA 與 NHI 資料。\n"
            "嚴格遵守四大結構輸出：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。\n"
            "格式要求：禁止粗體 (**)，條列式呈現。"
        )
    )

if "model" not in st.session_state:
    st.session_state.model = init_gemini()

# --- 3. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)

query = st.text_input("輸入藥品名稱、成分或代碼", placeholder="搜尋全資料庫藥品...", label_visibility="collapsed")

if query:
    # 這裡我們不直接執行 generate_content，而是放一個按鈕讓使用者觸發
    # 這樣可以避免輸入過程中不斷觸發 API 導致 429
    st.info(f"🔍 準備檢索：{query}")
    
    if st.button(f"確認搜尋並生成專業臨床報告"):
        with st.spinner(f"正在連線官方資料庫解析 {query}..."):
            try:
                # 執行搜尋
                response = st.session_state.model.generate_content(f"請分析台灣藥品 {query} 的健保與仿單數據。")
                result_text = response.text.replace('**', '')
                
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 0 0 0; color: white;">
                    <h3 style="margin: 0;">💊 專業報告：{query}</h3>
                </div>
                <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ 官方資料庫連線過於頻繁。請等待 20 秒，這是 Google API 的硬性限制。")
                    st.button("點擊此處重試")
                else:
                    st.error(f"❌ 發生錯誤：{e}")

st.divider()
st.caption("數據來源：即時連線中央健康保險署 (NHI) 與食藥署 (TFDA)")
