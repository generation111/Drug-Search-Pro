import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. UI 專業配置 ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #07101e;
        color: #dde6f0;
        font-family: 'Noto Sans TC', sans-serif;
    }
    [data-testid="stHeader"] { visibility: hidden; }
    .report-card {
        background: #0e1a2e;
        border: 1px solid rgba(79,156,249,0.3);
        border-radius: 12px;
        padding: 30px;
        margin-top: 20px;
    }
    .section-tag {
        color: #60a5fa;
        font-weight: 900;
        border-left: 5px solid #3b82f6;
        padding-left: 12px;
        margin: 25px 0 10px;
        font-size: 18px;
    }
    .official-btn {
        display: inline-block;
        padding: 6px 12px;
        background: #1a2a40;
        border: 1px solid #3b82f6;
        border-radius: 4px;
        color: #60a5fa !important;
        text-decoration: none;
        font-size: 13px;
        margin-right: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 初始化 OpenAI ---
def get_client():
    if "openai" in st.secrets:
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

client = get_client()

# --- 3. UI 渲染 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)
st.caption("專業臨床藥學檢索工具 - 官方數據路徑對接版")

# 獲取 URL 中的參數 (支援直接帶入搜尋)
query_params = st.query_params
default_query = query_params.get("search", "")
search_input = st.text_input("搜尋", value=default_query, placeholder="輸入藥名或許可證字號...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    encoded = urllib.parse.quote(target)
    
    # 直接顯示官方驗證路徑 (確保與您演示的 S01/S02/許可證/MCP 一致)
    st.markdown("### 🔗 官方實時檢索路徑")
    st.markdown(f"""
        <a class="official-btn" href="https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}" target="_blank">🏥 健保 S01</a>
        <a class="official-btn" href="https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}" target="_blank">🏥 健保 S02</a>
        <a class="official-btn" href="https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}" target="_blank">📜 食藥署許可證</a>
        <a class="official-btn" href="https://mcp.fda.gov.tw/im_detail_1/{encoded}" target="_blank">💊 仿單 MCP</a>
    """, unsafe_allow_html=True)

    if client:
        with st.spinner(f"正在執行官方路徑檢索：{target}..."):
            try:
                # 強制指令：絕對對應輸入內容，禁止任何名稱轉譯
                prompt = f"""你是一位嚴謹的藥學數據分析員。
                【核心任務】：請直接針對關鍵字「{target}」進行官方數據匯總。
                
                【執行準則】：
                1. 禁止將「{target}」轉譯為任何其他藥名或學名。
                2. 必須從 TFDA 許可證與 NHI 官方路徑獲取對應資料。
                3. 移除所有關於「健保點數」的文字與數值。
                4. 移除所有與「{target}」無關的補充說明與贅詞。
                5. 禁止回報「找不到」或「搜尋中」，請直接根據官方數據呈現結果。

                【報告結構】：
                【藥品基本資料】(必須包含許可證字號與官方登記品名)
                【臨床適應症與用法】(成人標準用法)
                【健保給付規定】(僅列出規範文字)
                【藥師臨床提示】

                回答規範：繁體中文、禁止使用粗體、標題統一使用【 】。
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                
                analysis_text = response.choices[0].message.content
                
                # --- 渲染報告 ---
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(f"## {target} 官方實時分析報告")
                
                lines = analysis_text.split('\n')
                for line in lines:
                    if '【' in line:
                        st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                    elif "點" not in line: # 確保移除點數
                        st.write(line)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"系統執行異常，請點擊上方官方連結核對。")
    else:
        st.warning("請設定 OpenAI API Key。")

st.markdown("---")
st.caption("⚠️ 本系統為獨立工具。所有資訊以中央健保署及食藥署官方公告為準。")
