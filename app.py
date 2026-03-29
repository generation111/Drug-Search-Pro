import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. 獨立系統樣式配置 ---
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
    
    /* 專業報告卡片樣式 */
    .report-card {
        background: #0e1a2e;
        border: 1px solid rgba(79,156,249,0.3);
        border-radius: 12px;
        padding: 30px;
        margin-top: 20px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.6);
    }
    
    /* 官方動態按鈕 */
    .official-btn {
        display: inline-block;
        padding: 10px 20px;
        margin: 5px;
        background: #1a2a40;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        color: #60a5fa !important;
        text-decoration: none;
        font-weight: 700;
        font-size: 14px;
        transition: 0.3s;
    }
    .official-btn:hover { background: #3b82f6; color: white !important; }
    
    .section-tag {
        color: #60a5fa;
        font-weight: 900;
        border-left: 5px solid #3b82f6;
        padding-left: 12px;
        margin: 25px 0 10px;
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 官方資料庫網址生成邏輯 ---
def generate_official_links(query_str):
    encoded = urllib.parse.quote(query_str)
    # 根據您提供的連結結構動態生成
    return {
        "NHI_S01": f"https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}",
        "NHI_S02": f"https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}",
        "TFDA_DRPIQ": f"https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}",
        "TFDA_MCP": f"https://mcp.fda.gov.tw/im_detail_1/{encoded}"
    }

# --- 3. UI 介面佈局 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)
st.caption("專業臨床藥學檢索工具 - 獨立運作版")

# 搜尋框
search_input = st.text_input("搜尋", placeholder="輸入藥名、成分或許可證字號 (如: Sheco, 012556, Bromhexine)", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    links = generate_official_links(target)
    
    # --- 顯示官方實時連結 ---
    st.markdown("### 🔗 官方實時檢索路徑")
    st.markdown(f"""
        <a class="official-btn" href="{links['NHI_S01']}" target="_blank">🏛️ 健保品項查詢 (S01)</a>
        <a class="official-btn" href="{links['NHI_S02']}" target="_blank">🏥 健保收載查詢 (S02)</a>
        <a class="official-btn" href="{links['TFDA_DRPIQ']}" target="_blank">📜 食藥署許可證</a>
        <a class="official-btn" href="{links['TFDA_MCP']}" target="_blank">💊 藥物外觀/仿單</a>
    """, unsafe_allow_html=True)

    # --- 4. AI 臨床解析 (不使用粗體，嚴格標題) ---
    if "openai" in st.secrets:
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        with st.spinner(f'解析「{target}」官方仿單數據中...'):
            try:
                # 強化 Prompt，確保所有藥品都能根據學名反推正確資料
                prompt = f"""你是一位資深臨床藥師。針對「{target}」進行專業分析。
                必須參考 TFDA 與 健保署 (NHI) 的標準規範。
                
                分析結構要求：
                1. 必須明確列出學名 (INN) 與常見商品名。
                2. 針對「{target}」在台灣的健保支付規範進行說明。
                3. 必須包含精確的用法用量 (如：成人1天3次)。
                4. 條列臨床注意事項。

                回答規範：繁體中文、不使用粗體、標題統一使用【 】。
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                
                analysis_text = response.choices[0].message.content
                
                # --- 渲染報告卡片 ---
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(f"## {target} 臨床分析報告")
                
                # 處理標題樣式渲染
                lines = analysis_text.split('\n')
                for line in lines:
                    if '【' in line:
                        st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                    else:
                        st.write(line)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"分析異常，請點擊上方官方連結確認資料。錯誤碼：{e}")
    else:
        st.warning("請設定 OpenAI API Key 以獲取 AI 臨床解析服務。")

st.markdown("---")
st.caption("⚠️ 本系統為獨立工具。所有資訊以 TFDA 官方仿單及健保署公告為準。")
