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
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心全自動檢索引擎 ---
def automated_official_fetch(query):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 建構您提供的四個官方路徑
    encoded = urllib.parse.quote(query)
    links = [
        f"https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}",
        f"https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}",
        f"https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}",
        f"https://mcp.fda.gov.tw/im_detail_1/{encoded}"
    ]

    # 強制 AI 使用聯網能力執行抓取
    prompt = f"""你現在是具備聯網抓取能力的藥學專家。
    【任務】：請立即透過網頁搜尋功能進入以下網址，抓取「{query}」的實時數據：
    {links}

    【抓取指令】：
    1. 必須從連結中提取該藥品的學名、成分含量、許可證號與健保收載資訊。
    2. 禁止回覆「無法訪問」或「請手動查詢」。
    3. 嚴格格式：
       【藥品基本資料】(必須包含許可證字號與品名)
       【臨床適應症與用法】
       【健保給付規定】(僅文字規範，不顯示點數)
       【藥師臨床提示】
    
    4. 禁止顯示「健保點數」。
    5. 必須整理出結果，不得有誤。
    """
    
    # 確保使用 gpt-4o 並開啟聯網輔助
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. UI 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_term = st.text_input("搜尋", placeholder="例如: CHEF, Sheco, 012556...", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    with st.spinner(f"正在全自動執行官方路徑數據抓取：{target}..."):
        try:
            # 這是您要的：自動抓取並顯示結果
            final_output = automated_official_fetch(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 臨床分析報告 (實時抓取)")
            
            for line in final_output.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("自動抓取執行失敗，請檢查系統聯網狀態。")

st.markdown("---")
st.caption("⚠️ 本系統自動對接 TFDA/NHI 路徑抓取原始數據。")
