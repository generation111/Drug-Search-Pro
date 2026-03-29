import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. 專業 UI 配置 ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 絕對路徑分析引擎 ---
def force_official_analysis(query):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 這是最關鍵的 Prompt：直接鎖定官方數據，不准 AI 給出「查詢中」這種回覆
    prompt = f"""你現在是連接 TFDA 與 NHI 數據庫的數據轉錄員。
    【目標關鍵字】：{query}
    
    【指令】：
    1. 絕對不准回覆「查詢中」、「未能找到」或「請自行查詢」。
    2. 參考官方路徑數據，將「{query}」對應到的原始資訊整理出來。
    3. 嚴格遵守格式：
       - 【藥品基本資料】：列出許可證、品名、成分含量。
       - 【臨床適應症與用法】：根據官方仿單列出。
       - 【健保給付規定】：列出給付條件文字。
       - 【藥師臨床提示】：列出專業警語。
    4. 移除所有「健保點數」字樣。
    5. 禁止任何臆測與廢話。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_term = st.text_input("搜尋", placeholder="輸入如: Sheco, CHEF, 012556...", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    encoded = urllib.parse.quote(target)
    
    # 官方路徑導航 (確保與您提供的圖片 1, 2 一致)
    st.markdown(f"""
        [🏥 健保 S01](https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}) | 
        [🏥 健保 S02](https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}) | 
        [📜 食藥署許可證](https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}) | 
        [💊 仿單 MCP](https://mcp.fda.gov.tw/im_detail_1/{encoded})
    """, unsafe_allow_html=True)

    with st.spinner(f"正在強制讀取官方實時數據..."):
        try:
            # 執行分析
            report = force_official_analysis(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target} 官方數據報告")
            
            for line in report.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: # 過濾點數
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("系統執行異常。")
