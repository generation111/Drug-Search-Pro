import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.9.5 (Column-Auto-Fix)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 雲端資料庫連接 ---
# 使用您的 Google Sheets 匯出連結
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/gviz/tq?tqx=out:csv&gid=1422349149"

@st.cache_data(ttl=300)
def load_cloud_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # 自動清洗欄位名稱：移除空格、換行，確保對接成功
        df.columns = [str(c).strip().replace('\n', '') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"資料庫載入失敗: {e}")
        return None

# --- 3. AI 分析引擎 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    # 此版本僅用於資料格式美化，不啟動 Live Search 以節省額度
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位台灣臨床藥師。請針對提供的資料庫數據進行整理。\n"
            "1. 必須區分同名異分藥品（如 CEFIN 對應之 Cephradine 與 Ceftriaxone）。\n"
            "2. 呈現欄位：健保代碼、藥品名稱、成分、規格、單價、廠商。\n"
            "3. 額外補充：Cephradine 配製後室溫僅保存 2 小時。\n"
            "4. 禁止使用粗體 (**)，使用簡潔清爽的列表。"
        )
    )
    return model

db_df = load_cloud_data()
model = init_gemini()

# --- 4. 介面介面 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>健保雲端同步版 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入搜尋關鍵字 (如: CEFIN)", placeholder="直接搜尋資料庫...", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    if db_df is not None:
        # 彈性搜尋邏輯：自動適應您的欄位名稱
        # 嘗試尋找包含 '藥品'、'成分' 字眼的欄位
        target_cols = [c for c in db_df.columns if '藥品' in c or '成分' in c or '名稱' in c]
        
        if not target_cols:
            st.error(f"資料庫欄位辨識失敗。目前的欄位有：{list(db_df.columns)}")
        else:
            # 在所有相關欄位中搜尋關鍵字
            mask = db_df[target_cols].apply(lambda x: x.str.contains(query, na=False, case=False)).any(axis=1)
            results = db_df[mask]
            
            if not results.empty:
                with st.spinner("專業藥師分析中..."):
                    # 將撈出的數據交給 AI
                    context = results.to_string(index=False)
                    prompt = f"以下是從健保資料庫搜尋到的結果，請整理成對照表單：\n\n{context}"
                    
                    try:
                        response = model.generate_content(prompt)
                        result_text = response.text.replace('**', '')
                        
                        st.markdown(f"""
                        <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                            <h3 style="margin: 0;">🔍 搜尋結果：{query}</h3>
                            <p style="font-size: 11px; color: #94a3b8; margin-top: 5px;">SOURCE: CLOUD DATABASE</p>
                        </div>
                        <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                        </div>
                        """, unsafe_allow_html=True)
                    except:
                        st.table(results) # 若 AI 額度限制，則直接顯示原始表格
            else:
                st.warning(f"查無資料：資料庫中找不到 '{query}'。")
    else:
        st.error("無法讀取雲端資料庫。")

st.divider()
st.caption("數據來源：健保雲端資料庫 | 慈榛驊有限公司")
