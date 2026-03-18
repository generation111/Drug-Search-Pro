import streamlit as st
import google.generativeai as genai
import time
import base64
import os  # <-- 必須補上這行，否則抓不到環境變數
from datetime import datetime

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.3.5"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide")

# 初始化 Session State (模擬 React 的 useState)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'cache' not in st.session_state:
    st.session_state.cache = {}

# --- 2. API 配置區塊 (自動偵測可用模型) ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["AIzaSyBxhnhHvPL6zBX_vA3R6Fs7tc8tsYU8YQM"]
    else:
        API_KEY = os.environ.get("AIzaSyBxhnhHvPL6zBX_vA3R6Fs7tc8tsYU8YQM", "")

    if not API_KEY or len(API_KEY) < 10:
        st.error("❌ 找不到有效的 API Key，請檢查 Secrets 設定。")
        st.stop()

    genai.configure(GEMINI_API_KEY)

    # 備選名單：從最穩定到最新版
    model_candidates = ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash']
    model = None

    for model_id in model_candidates:
        try:
            # 嘗試初始化模型
            test_model = genai.GenerativeModel(model_id)
            # 進行一次極小量的測試呼叫，確認 generateContent 權限
            test_model.generate_content("ping", generation_config={"max_output_tokens": 1})
            model = test_model
            # st.success(f"成功連結模型: {model_id}") # 除錯用，正常運作後可註解掉
            break
        except Exception:
            continue

    if model is None:
        st.error("❌ 目前無法連線至任何 Gemini 模型 (gemini-pro/1.5)。請檢查 API Key 是否有對應權限，或稍後再試。")
        st.stop()
    
except Exception as e:
    st.error(f"系統初始化異常: {e}")
    st.stop()
# --- 3. 自定義功能函數 ---
def export_html(query, content, duration, is_cached):
    """生成 HTML 報告供下載"""
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
        <div class="meta">產出時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        版本：{CURRENT_APP_VERSION}<br>分析耗時：{status}</div>
        <div class="content">{content.replace('**', '')}</div>
    </body></html>
    """
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="臨床報告_{query}.html" style="text-decoration:none;"><button style="background-color:#4F46E5; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:bold;">📥 導出報告</button></a>'

# --- 4. 介面佈局 ---
# 標題區塊 (CSS 強制置頂)
st.markdown("<h1 style='text-align: center; margin-top: -50px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>專業藥事情報系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

# 搜尋列
query = st.text_input("輸入藥品關鍵字...", placeholder="例如: Holisoon, Pregabalin...", label_visibility="collapsed")

# 顯示歷史紀錄 (模擬 Suggestions)
if st.session_state.history and not query:
    st.caption("最近搜尋： " + "、".join(st.session_state.history[:5]))

# --- 5. 核心邏輯：搜尋與分析 ---
if query:
    query = query.strip()
    start_time = time.time()
    result_text = ""
    is_cached = False

    # 檢查快取 (React Cache Logic)
    if query in st.session_state.cache:
        result_text = st.session_state.cache[query]
        is_cached = True
        duration = 0.0
    else:
        with st.spinner("🔄 正在同步雲端醫學數據..."):
            try:
                # 採用藥師視角的專業指令
                prompt = f"你是資深臨床藥師。請極速分析藥品 '{query}' 的適應症、用法、禁忌。分段清晰，不要使用粗體語法。"
                response = model.generate_content(prompt)
                result_text = response.text
                
                # 寫入快取與歷史
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
            status_color = "#22c55e" if is_cached else "#4F46E5"
            status_text = "快取即時讀取" if is_cached else f"分析耗時：{duration:.1f}s"
            st.markdown(f"<span style='color:{status_color}; font-size:12px; font-weight:bold; background:#f0fdf4; padding:4px 8px; border-radius:6px;'>● {status_text}</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(export_html(query, result_text, duration, is_cached), unsafe_allow_html=True)

        # 報告展示區
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 30px; border-radius: 20px 20px 0 0; margin-top: 20px;">
            <h2 style="color: white; margin: 0;">{query}</h2>
            <p style="color: #94a3b8; font-size: 10px; margin-top: 10px; letter-spacing: 1px;">CLINICAL REPORT V{CURRENT_APP_VERSION}</p>
        </div>
        <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 20px 20px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text.replace('**', '')}
        </div>
        """, unsafe_allow_html=True)

# --- 6. 頁尾 ---
st.divider()
st.caption(f"Rx Clinical Pro | 穩定版本: {CURRENT_APP_VERSION} | 雲端同步中")
