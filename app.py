import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "3.1.0 (Stable-Search-Logic)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 AI 引擎 (優化搜尋權重) ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    genai.configure(api_key=api_key)
    
    # 啟用搜尋工具以對接健保署與 TFDA
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        tools=[{"google_search_retrieval": {}}],
        system_instruction=(
            "你是一位資深台灣臨床藥師。請針對使用者提供的藥品關鍵字進行全資料庫檢索。\n\n"
            "【檢索與分析標準】：\n"
            "1. 資料來源：僅限台灣 TFDA 許可證與 NHI 健保署官方數據。\n"
            "2. 結構化輸出 (固定標題)：\n"
            "   - 【藥品基本資料】：包含成分、商品名、健保代碼與單價。\n"
            "   - 【臨床適應症與用法】：引用 TFDA 仿單核准用途與建議劑量。\n"
            "   - 【健保給付規定】：說明是否有特定科別限制或規範。\n"
            "   - 【藥師臨床提示】：重大副作用、穩定性、配製注意事项。\n\n"
            "【格式限制】：禁止使用粗體 (**)，使用簡潔條列式。"
        )
    )
    return model

# 使用 Streamlit 快取避免重複初始化
if "model" not in st.session_state:
    st.session_state.model = init_gemini()

# --- 3. 介面設計 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>台灣全藥品臨床搜尋引擎 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品名稱、成分或代碼 (如: SHECO, CEFIN, A012556109)", placeholder="搜尋全資料庫藥品...", label_visibility="collapsed")

if query:
    query = query.strip()
    
    with st.spinner(f"正在深度檢索 '{query}' 之臨床數據..."):
        # 增加些微延遲緩解 429 壓力
        time.sleep(1) 
        
        try:
            # 向 AI 發送搜尋與分析請求
            response = st.session_state.model.generate_content(f"請針對藥品 '{query}' 進行 NHI/TFDA 全數據檢索並產出四大結構臨床報告。")
            
            # 清理輸出格式
            result_text = response.text.replace('**', '')
            
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0; color: white;">
                <h3 style="margin: 0;">💊 藥事綜合報告：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px;">DATA SOURCE: NHI/TFDA REAL-TIME SEARCH</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            # 針對 429 錯誤提供優雅提示
            if "429" in str(e):
                st.warning("⚠️ 目前搜尋引擎請求過於頻繁。這通常發生在連續快速搜尋時。請稍等 10-20 秒後再嘗試，系統將自動恢復運作。")
            else:
                st.error(f"❌ 檢索中斷。錯誤訊息: {e}")

st.divider()
st.caption("數據來源：經由 AI 即時對接中央健康保險署與食藥署資料庫 | 僅供臨床藥事參考")
