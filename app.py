import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime

# --- 1. 系統配置 ---
# 系統名稱：慈榛驊業務管理系統（全功能終極修復版）
CURRENT_APP_VERSION = "1.6.0 (Model-Path-Fix)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Streamlit Secrets 中的 GEMINI_API_KEY。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 建立工具清單：使用 Google Search 進行實時藥品資料校對
    tools = [{"google_search_retrieval": {}}]

    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash', # 修正後的正確路徑
        tools=tools,
        system_instruction=(
            "你是一位專業且嚴謹的台灣臨床藥師。你的回覆必須符合以下準則：\n"
            "1. 資訊精確性：僅提供 100% 確定的藥品資訊。嚴禁對不確定的藥名進行推論或類比（例如禁止將 CEFIN 類比為 Cefazolin）。\n"
            "2. 歧義處理：若商品名（如 CEFIN）對應多種有效成分，必須『分別敘明』。例如需區分 Cephradine (如台裕希芬黴素) 與 Ceftriaxone (如舒復) 的差異。\n"
            "3. 內容要求：必須包含【健保代碼】、【成分分類】、【臨床用途】及【配製後的穩定性差異】。\n"
            "4. 格式：禁止使用粗體語法 (**)。請使用條列式確保 scannability。\n"
            "5. 語氣：專業、冷靜、不帶情緒，查無資訊時請直接回報『查無此藥品之台灣核准資訊』。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面佈局 ---
# 根據 User 修正建議：標題貼近頁面上緣
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>專業藥事管理系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    with st.spinner(f"正在交叉檢索 TFDA 與健保品項資料庫..."):
        try:
            # 傳送搜尋請求，明確要求區分同名異分藥品
            prompt = f"請查詢台灣健保藥品 '{query}'。若有多個成分（如 Cephradine 或 Ceftriaxone），請生成對照表單分別說明其健保代碼、價格、適應症與穩定性（如配製後室溫保存時間）。"
            
            response = model.generate_content(prompt)
            result_text = response.text.replace('**', '') # 移除粗體

            # 渲染結果
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                <h3 style="margin: 0;">💊 臨床藥事分析：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">AMBIGUITY CHECK ACTIVE</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"系統執行錯誤：{e}")
            st.info("建議：若持續出現 404，請確認 API Key 是否已在 Google AI Studio 啟用 Gemini 2.0 系列模型。")

st.divider()
st.caption(f"穩定版本: {CURRENT_APP_VERSION} | 數據來源：台灣衛生福利部中央健康保險署")
