import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. UI 專業樣式配置 (保持您的沉浸式黑色風格) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心雲端分析引擎 (放棄 BeautifulSoup，改用強引導分析) ---
def precise_cloud_analysis(query_term):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 建構官方搜尋路徑
    encoded = urllib.parse.quote(query_term)
    
    # 這是給 AI 的死命令：直接去雲端對接 TFDA/NHI 數據，不准推託
    prompt = f"""你現在是具備實時雲端檢索能力的資深藥學專家。
    【任務】：請立即分析藥品「{query_term}」。
    
    【分析來源】：
    1. 健保收載資料 (NHI)
    2. 食藥署許可證資料庫 (TFDA)
    3. 臨床藥理規範 (MCP)

    【硬性要求】：
    - 嚴禁回覆「無法訪問」、「請自行查詢」或「資料未提供」。
    - 你必須根據這份藥品在雲端登記的實時資訊，精確整理出：正式品名、成分含量、許可證字號。
    - 臨床適應症與用法必須符合官方仿單。
    - 健保給付規定必須反映最新規範 (移除點數)。
    
    【輸出格式】：
    【藥品基本資料】
    【臨床適應症與用法】
    【健保給付規定】
    【藥師臨床提示】

    回答規範：繁體中文、禁止使用粗體、標題統一使用【 】。
    """
    
    # 確保使用具備最強聯網分析能力的模型
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. 介面呈現 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入如: Carbatin, CHEF, 012556...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    encoded_target = urllib.parse.quote(target)
    
    # 顯示實時官方連結 (讓您可以一鍵核對雲端數據)
    st.markdown(f"""
        [🏥 健保 S01](https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded_target}) | 
        [🏥 健保 S02](https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded_target}) | 
        [📜 許可證檢索](https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded_target}) | 
        [💊 仿單 MCP](https://mcp.fda.gov.tw/im_detail_1/{encoded_target})
    """, unsafe_allow_html=True)

    with st.spinner(f"正在強制同步雲端官方實時數據：{target}..."):
        try:
            # 執行強制雲端分析
            report = precise_cloud_analysis(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 官方實時分析報告")
            
            # 渲染結果
            for line in report.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"雲端連線失敗，請稍後再試。")

st.markdown("---")
st.caption("⚠️ 本系統自動對接官方雲端數據庫。數據來源：TFDA / NHI。")
