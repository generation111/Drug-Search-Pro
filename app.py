import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS # 需 pip install duckduckgo-search

# --- 1. 專業 UI 配置 ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .info-box { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 強制搜尋邏輯 ---
def force_official_search(query):
    """強迫系統先去這四個站抓資料"""
    search_queries = [
        f"site:info.nhi.gov.tw {query} 健保價格",
        f"site:lmspiq.fda.gov.tw {query} 許可證",
        f"site:mcp.fda.gov.tw {query} 仿單 用法"
    ]
    raw_data = ""
    with DDGS() as ddgs:
        for q in search_queries:
            results = list(ddgs.text(q, max_results=2))
            for r in results:
                raw_data += f"\n來源: {r['href']}\n內容: {r['body']}\n"
    return raw_data

# --- 3. UI 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_term = st.text_input("輸入藥名", placeholder="例如: Sheco, Acetaminophen...", label_visibility="collapsed")

if search_term:
    with st.spinner(f"正在強制讀取 TFDA/NHI 實時數據..."):
        # 第一步：後台強行抓取資料，不靠 AI 猜
        official_raw_info = force_official_search(search_term)
        
        # 第二步：把抓到的死資料交給 AI 整理成專業格式
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        prompt = f"""你是一位藥師。以下是從 TFDA 與 NHI 網站抓取的原始數據：
        ---
        {official_raw_info}
        ---
        請針對「{search_term}」整理出精確報告。
        
        要求：
        1. 若數據含 Bromhexine 且使用者搜尋 Sheco，必須確認為 8mg 顆粒。
        2. 健保點數必須精確（參考 S02 數據）。
        3. 用法用量必須具體（如：1日3次）。
        4. 禁止出現「查詢中」或「無法確定」。
        5. 不使用粗體，標題用【 】。
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # --- 4. 渲染結果 ---
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(f"## {search_term} 臨床數據分析報告")
        
        output = response.choices[0].message.content
        for line in output.split('\n'):
            if '【' in line:
                st.markdown(f'<p style="color:#60a5fa; font-weight:900; margin-top:20px;">{line}</p>', unsafe_allow_html=True)
            else:
                st.write(line)
        st.markdown('</div>', unsafe_allow_html=True)
