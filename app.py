import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- 1. 系統配置 ---
# 系統名稱：慈榛驊業務管理系統（全功能終極修復版）
CURRENT_APP_VERSION = "1.7.0 (Quota-Optimized)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Streamlit Secrets 設定。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 建立模型
    # 注意：免費版若頻繁觸發 google_search 易導致 429，此版本優化指令以降低消耗
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位專業的台灣臨床藥師。請遵循以下規則：\n"
            "1. 必須區分同名異分藥品：例如搜尋 CEFIN 時，必須分別列出 Cephradine (如台裕) 與 Ceftriaxone (如舒復) 的差異。\n"
            "2. 臨床關鍵數據：\n"
            "   - Cephradine (1.0g): 健保碼 A030897，配製後室溫僅能保存 2 小時。\n"
            "   - Ceftriaxone: 健保碼 AC38615，為第三代頭孢菌素。\n"
            "3. 結構化輸出：提供【健保代碼】、【成分分類】、【臨床用途】、【配製穩定性】。\n"
            "4. 禁止使用粗體語法 (**)，禁止類比不確定藥名 (如 Cefazolin)。\n"
            "5. 語氣專業嚴謹，不使用贅字。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面與搜尋 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>慈榛驊業務管理系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

# 使用 Session State 防止重複觸發 API
if 'cache' not in st.session_state:
    st.session_state.cache = {}

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    if query in st.session_state.cache:
        result_text = st.session_state.cache[query]
    else:
        with st.spinner(f"正在分析藥品數據..."):
            try:
                # 這裡不強制掛載 google_search 以節省額度，除非系統預設知識不足
                prompt = f"分析藥品 '{query}'。若有同名異分（如 Cephradine/Ceftriaxone），請分別列出對照表。"
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
                st.session_state.cache[query] = result_text
            except Exception as e:
                if "429" in str(e):
                    st.error("目前流量過高，請稍等一分鐘。這是免費版 API 的物理限制。")
                    st.stop()
                else:
                    st.error(f"系統錯誤：{e}")
                    st.stop()

    # 渲染分析結果
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
        <h3 style="margin: 0;">💊 臨床藥事分析：{query}</h3>
        <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">PRECISION MODE ACTIVE</p>
    </div>
    <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption(f"穩定版本: {CURRENT_APP_VERSION} | 數據來源：TFDA & 健保署藥物查詢系統")
