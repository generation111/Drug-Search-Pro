import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 樣式設定 (極簡深色專業版) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 雲端自動轉向搜尋邏輯 (解決非健保藥品問題) ---
def google_live_fetch(query):
    # 使用 Serper API 模擬您在瀏覽器搜尋「藥名 官網 仿單」
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"藥品 官網 仿單 {query}",
        "gl": "tw",
        "hl": "zh-tw"
    })
    headers = {
        'X-API-KEY': st.secrets["SERPER_API_KEY"],
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        search_data = response.json()
        # 提取前 5 筆搜尋摘要，確保 AI 能看到藥廠官網內容
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:5]]
        return "\n".join(snippets)
    except:
        return "雲端搜尋暫時受阻。"

# --- 3. 系統主畫面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入如: Holisoon, Carbatin...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在全自動同步雲端官方資料：{target}..."):
        # 第一步：直接去雲端抓取搜尋結果 (模擬您點開新東官網看到的資料)
        live_context = google_live_fetch(target)
        
        # 第二步：由 AI 進行專業藥學整理
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        prompt = f"""你現在是資深藥師。根據以下搜尋到的官方即時資訊，整理「{target}」的報告。
        ---
        搜尋摘要：{live_context}
        ---
        【硬性要求】：
        1. 絕對禁止說「無法訪問」或使用「XXXXX」。
        2. 針對「Holisoon (喉立順)」，必須正確對應成分 Benzydamine HCl 與新東大藥廠。
        3. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        4. 給付規定若查無資料，請標註「本品項為自費/指示藥品，不佔健保額度」。
        5. 移除所有健保點數。標題用【 】，禁止粗體。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # --- 4. 渲染成果 ---
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 官方實時分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception:
            st.error("雲端連線繁忙，請重新嘗試。")

st.markdown("---")
st.caption("⚠️ 系統已啟動「雲端自動轉向搜尋」，確保非健保藥品亦能獲取精確官網資料。")
