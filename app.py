import streamlit as st
import google.generativeai as genai
import time
import base64
import os
from datetime import datetime

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.5.5 (Clinical Grounding)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# 初始化 Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'cache' not in st.session_state:
    st.session_state.cache = {}

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請在 Streamlit Secrets 設定: GEMINI_API_KEY")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 建立具備「專業臨床藥師」性格的模型
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=(
            "你是一位深耕台灣醫藥市場的資深臨床藥師。你的任務是針對使用者查詢的藥品進行精準分析。\n"
            "1. 必須優先檢索並引用：台灣衛福部食藥署 (TFDA) 許可證、健保署 (NHI) 健保用藥品項查詢系統 (包含健保代碼與最新價格)。\n"
            "2. 輸出格式規範：\n"
            "   - 【基本資料】：成分、商品名、健保代碼與價格。\n"
            "   - 【臨床用途】：台灣核准適應症與用法用量。\n"
            "   - 【健保給付規定】：是否有特殊規範 (如限制科別、需事前審查等)。\n"
            "   - 【藥師臨床提示】：禁忌、副作用、配製注意事項。\n"
            "3. 語氣要求：繁體中文、專業嚴謹、分段清晰，禁止使用粗體語法 (**)。"
        )
    )
    return model

model = init_gemini()

# --- 3. 報告導出函數 ---
def export_html(query, content, duration, is_cached):
    status = "本地快取" if is_cached else f"{duration:.1f} 秒"
    html_content = f"""
    <html>
    <head><meta charset="utf-8"><style>
        body {{ font-family: sans-serif; line-height: 1.6; padding: 40px; color: #333; }}
        h1 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        .content {{ white-space: pre-wrap; background: #f8fafc; padding: 20px; border-radius: 8px; }}
    </style></head>
    <body>
        <h1>臨床藥事報告：{query}</h1>
        <div class="meta">產出時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>來源：Rx Clinical Pro (V{CURRENT_APP_VERSION})</div>
        <div class="content">{content}</div>
    </body></html>
    """
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="臨床報告_{query}.html" style="text-decoration:none;"><button style="background-color:#4F46E5; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:bold;">📥 導出 HTML 報告</button></a>'

# --- 4. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -50px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>專業藥品資料庫對應系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字 (如: Cefin, Holisoon...)", placeholder="輸入搜尋關鍵字...", label_visibility="collapsed")

if st.session_state.history and not query:
    st.caption("🔍 最近搜尋： " + "、".join(st.session_state.history[:5]))

# --- 5. 搜尋與分析邏輯 ---
if query:
    query = query.strip()
    start_time = time.time()
    result_text = ""
    is_cached = False

    # 檢查快取
    if query in st.session_state.cache:
        result_text = st.session_state.cache[query]
        is_cached = True
        duration = 0.0
    else:
        with st.spinner(f"🔄 正在檢索台灣健保與 TFDA 數據庫分析 {query}..."):
            try:
                # 啟用 Google Search 工具進行實時檢索
                response = model.generate_content(
                    f"請詳細分析藥品 '{query}' 的健保給付與臨床資訊。",
                    tools=[{'google_search': {}}]
                )
                result_text = response.text.replace('**', '') # 移除粗體語法
                st.session_state.cache[query] = result_text
                if query not in st.session_state.history:
                    st.session_state.history.insert(0, query)
                duration = time.time() - start_time
            except Exception as e:
                st.error(f"分析失敗: {e}")

    # 顯示結果
    if result_text:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"⏱️ {'快取即時讀取' if is_cached else f'搜尋耗時：{duration:.1f}s'}")
        with col2:
            st.markdown(export_html(query, result_text, duration, is_cached), unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 30px; border-radius: 20px 20px 0 0; margin-top: 20px; color: white;">
            <h2 style="margin: 0; color: white;">{query}</h2>
            <p style="color: #94a3b8; font-size: 11px; margin-top: 10px; letter-spacing: 1px;">DATABASE GROUNDING ACTIVE</p>
        </div>
        <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 20px 20px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption(f"Rx Clinical Pro | 穩定版本: {CURRENT_APP_VERSION}")
