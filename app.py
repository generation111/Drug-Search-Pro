import streamlit as st

# --- 0. 環境檢查 ---
try:
    import requests
    from bs4 import BeautifulSoup
    from openai import OpenAI
except ImportError:
    st.error("⚠️ 偵測到環境設定未完成！請在 GitHub 的 requirements.txt 加入：openai, requests, beautifulsoup4")
    st.stop()

import urllib.parse

# --- 1. UI 樣式 (保持您要的專業深色調) ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 強行抓取邏輯 (不再靠 AI 猜，由 Python 去拿) ---
def crawl_official_site(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=8)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        # 僅保留純文字，過濾掉 JS 指令
        return soup.get_text()[:1500] 
    except:
        return "無法讀取該路徑。"

# --- 3. 執行引擎 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋", placeholder="輸入如: CHEF, Sheco...", label_visibility="collapsed")

if query:
    target = query.strip()
    encoded = urllib.parse.quote(target)
    
    # 定義官方路徑
    paths = {
        "S01": f"https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}",
        "S02": f"https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}",
        "TFDA": f"https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}",
        "MCP": f"https://mcp.fda.gov.tw/im_detail_1/{encoded}"
    }

    with st.spinner(f"正在強制對接官方資料庫抓取：{target}..."):
        # Python 先動手抓取
        raw_data = ""
        for key, url in paths.items():
            raw_data += f"\n[來源 {key}]\n{crawl_official_site(url)}\n"

        # 交給 AI 整理
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        prompt = f"你是藥學數據整理員，以下是從官網抓取的原始內容：\n{raw_data}\n\n請根據以上內容整理「{target}」的報告，嚴格移除健保點數，格式必須包含【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。標題用【 】，不准用粗體。"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # 渲染結果
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(f"## {target.upper()} 官方實時抓取報告")
        for line in response.choices[0].message.content.split('\n'):
            if '【' in line:
                st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
            elif "點" not in line:
                st.write(line)
        st.markdown('</div>', unsafe_allow_html=True)

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
