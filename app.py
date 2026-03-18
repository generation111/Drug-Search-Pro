import streamlit as st
import google.generativeai as genai
import time
import base64
import os
from datetime import datetime

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.3.6"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide")

# 初始化狀態
if 'history' not in st.session_state:
    st.session_state.history = []
if 'cache' not in st.session_state:
    st.session_state.cache = {}

# --- 2. 核心 API 配置 (最強容錯版) ---
def init_gemini():
    # 嘗試從各種路徑抓取金鑰
    api_key = None
    
    # 優先順序 1: Streamlit Secrets 標籤名 GEMINI_API_KEY
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    # 優先順序 2: 如果你誤把金鑰內容當成標籤 (修正你之前的錯誤)
    elif "AIzaSyBxhnhHvPL6zBX_vA3R6Fs7tc8tsYU8YQM" in st.secrets:
        api_key = "AIzaSyBxhnhHvPL6zBX_vA3R6Fs7tc8tsYU8YQM"
    # 優先順序 3: 環境變數
    else:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        st.error("❌ 找不到 API 金鑰。請在 Streamlit Secrets 設定: GEMINI_API_KEY = '你的金鑰'")
        st.stop()

    try:
        genai.configure(api_key=api_key)
        # 解決 404 問題：直接指定最穩定的名稱
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"模型初始化失敗: {e}")
        st.stop()

model = init_gemini()

# --- 3. 自定義功能函數 ---
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
        <div class="meta">產出時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>版本：{CURRENT_APP_VERSION}</div>
        <div class="content">{content.replace('**', '')}</div>
    </body></html>
    """
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="臨床報告_{query}.html" style="text-decoration:none;"><button style="background-color:#4F46E5; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:bold;">📥 導出報告</button></a>'

# --- 4. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -50px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字...", placeholder="例如: Holisoon...", label_visibility="collapsed")

if st.session_state.history and not query:
    st.caption("最近搜尋： " + "、".join(st.session_state.history[:5]))

# --- 5. 搜尋邏輯 ---
if query:
    query = query.strip()
    start_time = time.time()
    result_text = ""
    is_cached = False

    if query in st.session_state.cache:
        result_text = st.session_state.cache[query]
        is_cached = True
        duration = 0.0
    else:
        with st.spinner("🔄 正在分析數據..."):
            try:
                prompt = f"你是資深臨床藥師。請分析藥品 '{query}' 的適應症、用法、禁忌。分段清晰，不要使用粗體語法。"
                response = model.generate_content(prompt)
                result_text = response.text
                st.session_state.cache[query] = result_text
                if query not in st.session_state.history:
                    st.session_state.history.insert(0, query)
                duration = time.time() - start_time
            except Exception as e:
                st.error(f"分析失敗: {e}")

    if result_text:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"● {'快取即時讀取' if is_cached else f'耗時：{duration:.1f}s'}")
        with col2:
            st.markdown(export_html(query, result_text, duration, is_cached), unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 30px; border-radius: 20px 20px 0 0; margin-top: 20px; color: white;">
            <h2 style="margin: 0;">{query}</h2>
        </div>
        <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 20px 20px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text.replace('**', '')}
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption(f"Rx Clinical Pro | V{CURRENT_APP_VERSION}")
