import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- 1. UI 專業配置 ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 強力抓取函數 (代替人工點擊) ---
def get_raw_web_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # 抓取主要文字內容，過濾掉選單腳本
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()[:2000] # 限制長度避免 Token 爆炸
    except:
        return ""

# --- 3. 核心處理邏輯 ---
def process_drug_analysis(query):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    encoded = urllib.parse.quote(query)
    
    # 這是您要求的四個官方入口
    paths = {
        "NHI_S01": f"https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}",
        "NHI_S02": f"https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}",
        "TFDA": f"https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}",
        "MCP": f"https://mcp.fda.gov.tw/im_detail_1/{encoded}"
    }

    # 第一步：Python 先幫 AI 抓資料
    all_context = ""
    for name, url in paths.items():
        all_context += f"\n--- 來源 {name} ---\n{get_raw_web_data(url)}\n"

    # 第二步：強迫 AI 整理這些抓到的死資料
    prompt = f"""你是數據整理員。以下是從 TFDA/NHI 網站直接抓取的原始 HTML 文字：
    ---
    {all_context}
    ---
    請根據上述實時數據，整理「{query}」的報告。
    要求：
    1. 絕對禁止回覆「無法訪問」或「請自行搜尋」，因為資料就在上面。
    2. 移除所有「健保點數」。
    3. 嚴格對接許可證字號與成分內容。
    4. 標題統一使用【 】。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 4. 介面渲染 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_term = st.text_input("搜尋", placeholder="輸入如: CHEF, Sheco...", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    with st.spinner(f"正在強行對接官方路徑抓取數據：{target}..."):
        try:
            report = process_drug_analysis(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 臨床分析報告 (實時抓取)")
            
            for line in report.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"連線失敗，請檢查網路。")

st.markdown("---")
st.caption("⚠️ 本系統強制執行官方網站內容抓取。")
