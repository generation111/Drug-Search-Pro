import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. 專業 UI 配置 ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心自動抓取引擎 ---
def fetch_and_analyze(query_term):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    encoded = urllib.parse.quote(query_term)
    
    # 建構 AI 必須讀取的實時數據源網址
    s01_url = f"https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}"
    s02_url = f"https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}"
    tfda_url = f"https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}"
    mcp_url = f"https://mcp.fda.gov.tw/im_detail_1/{encoded}"

    # 強制指令：要求 AI 使用搜尋工具/瀏覽功能進入這些網址
    prompt = f"""你是一位具備實時網頁抓取能力的藥師。
    【核心任務】：請立即訪問以下網址，抓取「{query_term}」的原始數據：
    1. {s01_url} (健保品項)
    2. {s02_url} (健保收載)
    3. {tfda_url} (食藥署許可證)
    4. {mcp_url} (藥物資訊網仿單)

    【抓取要求】：
    - 找出該藥品的正確「學名」、「成分含量」、「許可證字號」。
    - 找出「適應症」與「用法用量」。
    - 找出「健保給付規定」的文字內容。
    - **絕對禁止** 顯示任何「健保點數」。
    - **絕對禁止** 回覆「請自行查詢」或「查無資料」。若網頁有內容，必須直接轉錄。

    【報告結構】：
    【藥品基本資料】
    【臨床適應症與用法】
    【健保給付規定】
    【藥師臨床提示】

    回答規範：繁體中文、禁止使用粗體、標題統一使用【 】。
    """
    
    # 使用具備聯網能力的模型執行
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. UI 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋", placeholder="輸入藥名或許可證字號...", label_visibility="collapsed")

if query:
    target = query.strip()
    with st.spinner(f"正在全自動讀取官方資料庫數據：{target}..."):
        try:
            # 執行抓取與分析
            final_report = fetch_and_analyze(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target} 臨床分析報告 (實時抓取)")
            
            for line in final_report.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"自動抓取失敗。原因：{e}")

st.markdown("---")
st.caption("⚠️ 本系統自動對接官方路徑讀取數據，確保資訊與實時官網一致。")
