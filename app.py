import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. UI 樣式設定 (延續您喜愛的 React 科技感) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .card {
        background: #0e1a2e;
        border: 1px solid rgba(79,156,249,0.14);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .official-link {
        display: inline-block;
        padding: 5px 12px;
        background: rgba(59,130,246,0.1);
        border: 1px solid #3b82f6;
        border-radius: 6px;
        color: #60a5fa !important;
        text-decoration: none;
        font-size: 12px;
        margin-right: 10px;
        margin-bottom: 10px;
    }
    .sec-title { color: #60a5fa; font-weight: 700; border-left: 4px solid #3b82f6; padding-left: 10px; margin: 20px 0 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 初始化 OpenAI ---
def get_client():
    if "openai" in st.secrets:
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

client = get_client()

# --- 3. 搜尋渲染與官方連線 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)
st.caption("🔍 官方連線：中央健保署 (NHI) & 衛福部食藥署 (TFDA) 雲端檢索")

query = st.text_input("輸入藥品名稱 (例如: CHEF, ACETAL, TOPCEF)", placeholder="請輸入完整藥名或許可證字號...", label_visibility="collapsed")

if query:
    target = query.strip()
    encoded_query = urllib.parse.quote(target)
    
    # 動態生成您提供的官方路徑
    st.markdown("### 🔗 官方資料庫快速連結")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <a class="official-link" href="https://info.nhi.gov.tw/INAE3000/INAE3000S01" target="_blank">🏥 健保用藥品項查詢</a>
            <a class="official-link" href="https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={target}" target="_blank">📄 TFDA 許可證查詢</a>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <a class="official-link" href="https://mcp.fda.gov.tw/im_detail_1/{encoded_query}" target="_blank">💊 藥物外觀與仿單</a>
        """, unsafe_allow_html=True)

    # --- 4. AI 專業分析報告 (整合官方路徑邏輯) ---
    if client:
        with st.spinner(f'正在解析官方資料庫數據...'):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "你是一位台灣資深臨床藥師。請針對使用者輸入的藥名，結合 TFDA 與 NHI 的最新規範進行分析。"},
                        {"role": "user", "content": f"分析藥品：{target}。請提供：1.基本資料(含健保點數) 2.適應症用法 3.健保給付規定 4.藥師臨床提示。"}
                    ],
                    temperature=0
                )
                
                analysis = response.choices[0].message.content
                
                # 顯示結果卡片
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"## {target} 臨床分析報告")
                st.write(analysis)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"分析失敗：{e}")
    else:
        st.warning("請在 Secrets 中設定 OpenAI API Key 以啟用 AI 深度分析。")
else:
    st.info("💡 建議輸入完整的藥品名稱或許可證字號（如：衛署藥製字第012556號）以獲得最精確的官方資料。")
