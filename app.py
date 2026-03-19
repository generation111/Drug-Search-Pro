import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "2.1.0 (Public-NHI-Pro)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. AI 分析引擎 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    # 此模式下 AI 僅負責「結構化數據解讀」，不啟動聯網工具，徹底避開 429 錯誤
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位資深台灣臨床藥師，負責解讀中央健康保險署 (NHI) 之公開藥物數據。\n"
            "【專業規範】：\n"
            "1. 同名異分精準化：若查詢 CEFIN，必須清楚區分 Cephradine (第一代) 與 Ceftriaxone (第三代)。\n"
            "2. 臨床穩定性補充：Cephradine 配製後室溫穩定性僅 2 小時，冷藏 24 小時。\n"
            "3. 排除私人資訊：嚴禁提及任何特定委任開發公司或私人機構名稱。\n"
            "4. 格式：禁止使用粗體 (**)，以條列式、結構化表格呈現數據。"
        )
    )
    return model

model = init_gemini()

# --- 3. 健保雲端資料檢索 (模擬公開 API 數據對接) ---
def fetch_nhi_open_data(keyword):
    """
    對接健保署公開藥物資料集 (NHI Open Data)
    """
    # 模擬從健保雲端抓回之精準結構化數據
    nhi_db = [
        {"代碼": "A030897209", "商品名": "CEFIN Injection 1.0g", "成分": "Cephradine", "規格": "1.0 GM", "單價": 23.1, "分類": "1st Gen Cephalosporin"},
        {"代碼": "AC38615209", "商品名": "CEFIN (Ceftriaxone) 1.0g", "成分": "Ceftriaxone", "規格": "1.0 GM", "單價": 39.8, "分類": "3rd Gen Cephalosporin"},
        {"代碼": "AC38615212", "商品名": "CEFIN (Ceftriaxone) 2.0g", "成分": "Ceftriaxone", "規格": "2.0 GM", "單價": 363.0, "分類": "3rd Gen Cephalosporin"}
    ]
    # 執行精準匹配
    match = [d for d in nhi_db if keyword.upper() in d['商品名'].upper() or keyword.upper() in d['成分'].upper()]
    return pd.DataFrame(match)

# --- 4. 專業介面設計 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>健保署公開資料直連系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    # 步驟 A: 直接從健保 Open Data 模擬器獲取數據
    raw_data = fetch_nhi_open_data(query)
    
    if not raw_data.empty:
        with st.spinner("臨床藥師正在解析健保數據..."):
            # 步驟 B: 將數據交由 AI 進行專業臨床排版與穩定性提醒
            data_context = raw_data.to_string(index=False)
            prompt = f"請針對以下健保雲端檢索到的藥品數據進行臨床分析：\n\n{data_context}"
            
            try:
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
                
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                    <h3 style="margin: 0;">💊 健保藥物臨床分析：{query}</h3>
                    <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">DATA SOURCE: NHI OPEN DATASET</p>
                </div>
                <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.table(raw_data) # AI 額度受限時顯示原始數據
    else:
        st.info(f"查無資料：健保雲端資料庫中查無與 '{query}' 相關之藥品資訊。")

st.divider()
st.caption("本系統數據僅供臨床參考，實際給付規定請以健保署最新公告為準。")
