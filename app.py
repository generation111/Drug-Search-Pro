import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 系統配置 ---
# 系統代號：慈榛驊業務管理系統（全功能終極修復版）
CURRENT_APP_VERSION = "1.9.0 (DB-First-Logic)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 雲端資料庫連接 (Google Sheets) ---
# 這裡使用您提供的試算表代號
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FREJX9NPtyVcAG1jou4jD0MjbAVoW-treZTpsmehCks/gviz/tq?tqx=out:csv&gid=1422349149"

@st.cache_data(ttl=600)  # 快取 10 分鐘，避免頻繁讀取雲端
def load_cloud_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        return None

# --- 3. AI 分析引擎配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位專業臨床藥師。你的任務是『解讀資料庫數據』。\n"
            "1. 嚴禁自行發想或類比。僅針對提供的資料庫內容進行排版。\n"
            "2. 同名異分處理：若資料庫內有多筆同名但不同成分（如 CEFIN），必須分別列出對照表。\n"
            "3. 核心數據：必須包含健保代碼、成分、規格、單價、穩定性說明。\n"
            "4. 格式：禁止使用粗體 (**)，使用簡潔條列式。"
        )
    )
    return model

db_df = load_cloud_data()
model = init_gemini()

# --- 4. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>雲端資料庫同步版 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字 (商品名/成分)", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    # 步驟 A: 先從雲端資料庫過濾資料 (完全不消耗 API)
    if db_df is not None:
        # 搜尋商品名或成分名包含關鍵字的資料
        results = db_df[
            db_df['藥品名稱(英文)'].str.contains(query, na=False, case=False) | 
            db_df['成分名稱'].str.contains(query, na=False, case=False)
        ]
        
        if not results.empty:
            with st.spinner("正在由 AI 整理臨床對照表..."):
                # 步驟 B: 將資料庫撈出的正確數據交給 AI 進行美化排版
                # 這樣 AI 只負責「文字處理」，不會去啟動昂貴的「聯網搜尋」
                db_context = results.to_string(index=False)
                prompt = f"以下是資料庫查得之藥品數據，請為臨床醫師整理成專業對照表：\n\n{db_context}"
                
                try:
                    response = model.generate_content(prompt)
                    result_text = response.text.replace('**', '')
                    
                    st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                        <h3 style="margin: 0;">💊 雲端資料庫查詢：{query}</h3>
                        <p style="font-size: 11px; color: #94a3b8; margin-top: 5px;">DATABASE SOURCE: 表單回應 1</p>
                    </div>
                    <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI 整理失敗：{e}")
        else:
            st.warning(f"查無資料：資料庫中找不到與 '{query}' 相關的藥品。")
    else:
        st.error("無法連線至雲端資料庫，請檢查 Google Sheets 分享權限。")

st.divider()
st.caption("慈榛驊有限公司 版權所有 | 數據同步來源：Google Sheets")
