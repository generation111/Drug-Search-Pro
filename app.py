import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 系統環境配置 ---
CURRENT_APP_VERSION = "3.0.0 (Global-Search-Engine)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. AI 臨床藥師引擎 (具備 Google 搜尋功能) ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
        st.stop()
    genai.configure(api_key=api_key)
    
    # 啟用 google_search 檢索工具以實現「搜尋所有藥品」
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        tools=[{"google_search_retrieval": {}}], 
        system_instruction=(
            "你是一位資深台灣臨床藥師。你的任務是搜尋台灣食藥署(TFDA)與健保署(NHI)資料庫，為使用者提供精準的藥品報告。\n\n"
            "【搜尋與分析邏輯】：\n"
            "1. 當使用者輸入藥品名稱或代碼時，請優先使用 Google Search 搜尋該藥品的『TFDA 許可證詳細資料』與『健保給付代碼/單價』。\n"
            "2. 必須嚴格依照以下四大結構進行排版報告：\n"
            "   - 【藥品基本資料】：成分、商品名、健保代碼與最新單價。\n"
            "   - 【臨床適應症與用法】：引用 TFDA 核准之用途與建議劑量。\n"
            "   - 【健保給付規定】：說明是否有特定科別限制、需附報告等給付規範。\n"
            "   - 【藥師臨床提示】：包含重大副作用、交互作用、配製注意事项(如穩定性)。\n\n"
            "【限制條件】：\n"
            "- 禁止使用粗體 (**)，使用簡潔清爽的列表呈現。\n"
            "- 引用資料時，請確保資訊來自台灣官方網站 (mcp.fda.gov.tw 或 info.nhi.gov.tw)。"
        )
    )
    return model

model = init_gemini()

# --- 3. 前端介面設計 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>台灣藥訊即時檢索系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

# 模仿健保署查詢介面
query = st.text_input("請輸入藥品名稱、成分或健保代碼進行全資料庫搜尋", placeholder="例如: 捨咳, CEFIN, 或 A012556109", label_visibility="collapsed")

if query:
    query = query.strip()
    
    with st.spinner(f"正在連線健保署與 TFDA 資料庫檢索 '{query}'..."):
        try:
            # AI 執行即時搜尋並進行四大結構分析
            # 這裡不再受限於內建清單，AI 會去網路上找最新資料
            response = model.generate_content(f"請搜尋藥品 '{query}' 的完整資訊並製作臨床分析報告。")
            
            # 清除粗體格式
            result_text = response.text.replace('**', '')
            
            # 渲染專業報告頁面
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0; color: white;">
                <h3 style="margin: 0;">💊 藥事綜合報告：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">REAL-TIME DATA FROM NHI & TFDA</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ 搜尋流量過大，請稍候 30 秒再試一次。")
            else:
                st.error(f"❌ 檢索失敗，請確認藥品名稱是否正確。錯誤訊息: {e}")

st.divider()
st.caption("聲明：本系統數據經由 AI 即時檢索台灣官方資料庫生成，僅供臨床藥事參考，實際給付規範請以健保署最新公告為準。")
