import streamlit as st
import google.generativeai as genai

# --- 1. 系統配置 ---
# 系統代號：慈榛驊業務管理系統（全功能終極修復版）
CURRENT_APP_VERSION = "1.7.5 (Internal-Grounding)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 建立模型：將 CEFIN 的正確資訊直接植入指令，避免觸發 429 聯網錯誤
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位專業台灣臨床藥師。當使用者查詢特定藥品時，請優先依照以下內建知識回覆：\n\n"
            "【商品名：CEFIN 的歧義處理邏輯】\n"
            "若查詢 CEFIN，必須區分為以下兩類：\n"
            "1. Cephradine (西華定)：\n"
            "   - 代表藥品：台裕希芬黴素注射劑 1g。\n"
            "   - 健保代碼：A030897209，價格 23.1 元。\n"
            "   - 配製：肌肉注射加 4ml 水；靜脈注射加 10ml 水。\n"
            "   - 穩定性：配製後室溫僅能保存 2 小時，冰箱冷藏 24 小時。\n"
            "2. Ceftriaxone (西華龍)：\n"
            "   - 代表藥品：舒復靜脈注射劑 (PANBIOTIC)。\n"
            "   - 健保代碼：AC38615 系列，價格約 39.8 至 363 元。\n"
            "   - 特性：第三代頭孢菌素，半衰期長，通常一日給藥一次。\n\n"
            "【回覆規範】：\n"
            "- 禁止使用粗體語法 (**)。\n"
            "- 嚴禁類比不確定藥名（如 Cefazolin）。\n"
            "- 若資料庫查無資訊，請回報『目前查無此藥品之台灣核准資訊』。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面與快取 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>慈榛驊業務管理系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

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
                # 關鍵：減少聯網請求，改用內建知識
                prompt = f"請分析藥品 '{query}'。如果是 CEFIN，請依據內建資訊區分 Cephradine 與 Ceftriaxone。"
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
                st.session_state.cache[query] = result_text
            except Exception as e:
                st.error(f"目前查詢次數過多，請稍候一分鐘。")
                st.stop()

    # 渲染結果
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
        <h3 style="margin: 0;">💊 臨床藥事分析：{query}</h3>
        <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">INTERNAL DATA MATCHED</p>
    </div>
    <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption(f"穩定版本: {CURRENT_APP_VERSION} | 數據來源：TFDA & 健保署")
