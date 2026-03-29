import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- 1. UI 專業配置 ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 實體抓取函數 (代替人工進入網站) ---
def crawl_official_data(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # 移除無關的腳本與樣式，只留文字
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()[:2000] # 抓取前 2000 字餵給 AI
    except:
        return ""

# --- 3. 執行邏輯 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_term = st.text_input("搜尋", placeholder="輸入如: CHEF, Sheco...", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    encoded = urllib.parse.quote(target)
    
    # 建立官方路徑
    paths = {
        "NHI_S01": f"https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}",
        "NHI_S02": f"https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}",
        "TFDA": f"https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}",
        "MCP": f"https://mcp.fda.gov.tw/im_detail_1/{encoded}"
    }

    with st.spinner(f"正在強制對接官方路徑抓取數據：{target}..."):
        # 第一步：由 Python 實體執行抓取 (不再靠 AI 猜)
        context_data = ""
        for name, url in paths.items():
            context_data += f"\n--- 來源 {name} ---\n{crawl_official_data(url)}\n"

        # 第二步：將抓到的實體內容交給 AI 整理
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        prompt = f"""你是一位專業藥師。以下是從 TFDA/NHI 網站直接抓取的實時數據內容：
        ---
        {context_data}
        ---
        請根據上述「實體數據」整理「{target}」的報告。
        
        【要求】：
        1. 絕對禁止回覆「無法訪問」或「請自行搜尋」，資料已在上方。
        2. 嚴格提取：藥品名稱、成分含量、許可證字號。
        3. 移除所有「健保點數」。
        4. 格式包含：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        5. 標題統一使用【 】，禁止使用粗體。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # --- 4. 渲染結果 ---
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 官方實時分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("分析引擎調用失敗。")

st.markdown("---")
st.caption("⚠️ 本系統強制執行官方網站內容抓取，數據以 TFDA/NHI 為準。")
