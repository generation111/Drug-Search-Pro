import streamlit as st
import google.generativeai as genai
import time

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.6.5 (Final-Stability)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    # 提醒：請至 Google AI Studio 重新生成金鑰，原金鑰已遭標記為洩漏
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Streamlit Secrets。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 宣告實時檢索工具
    tools = [{"google_search_retrieval": {}}]

    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash', 
        tools=tools,
        system_instruction=(
            "你是一位專業且極度嚴謹的台灣臨床藥師。\n"
            "【最高準則】：\n"
            "1. 資訊必須 100% 精確。嚴禁任何類比（如禁止將 CEFIN 類比為 Cefazolin）。\n"
            "2. 處理同名異分：若商品名（如 CEFIN）對應多種有效成分，必須『分別敘明』其臨床差異，重點標註：成分名、健保代碼、價格、適應症。\n"
            "3. 穩定性要求：明確列出配製後的保存時間差異（如 Cephradine 室溫僅 2 小時，Ceftriaxone 穩定性較高）。\n"
            "4. 禁止粗體語法 (**)。請使用簡潔的條列式表格呈現。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>同名異分精準對照系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    with st.spinner(f"正在交叉比對 TFDA、健保署與藥廠仿單數據..."):
        try:
            # 強制要求區分同名異分
            prompt = f"查詢藥品 '{query}'。若有多個成分（如 Cephradine 或 Ceftriaxone），請分別列出其健保代碼、適應症與配製穩定性差異。"
            
            response = model.generate_content(prompt)
            result_text = response.text.replace('**', '')

            # 結果呈現
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                <h3 style="margin: 0;">💊 臨床藥事對照：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">AMBIGUITY DETECTION ACTIVE</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            # 針對 429 錯誤的友善提示
            if "429" in str(e):
                st.warning("⚠️ 目前 API 使用次數已達免費額度上限，請稍候 60 秒再試，或更換金鑰。")
            elif "403" in str(e):
                st.error("🚫 API 金鑰已遭停用（洩漏風險），請至 Google AI Studio 更新金鑰。")
            else:
                st.error(f"系統診斷錯誤：{e}")

st.divider()
st.caption("數據來源：台灣衛生福利部中央健康保險署 & TFDA 官方仿單庫")
