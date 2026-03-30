import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 配置 (保持專業深色調) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心搜尋邏輯：當官網查無資料時，強制執行 Google 搜尋 ---
def search_google_live(query):
    # 使用 Serper API 模擬 Google 搜尋
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"TFDA 藥物外觀 仿單 {query}",
        "gl": "tw",
        "hl": "zh-tw"
    })
    headers = {
        'X-API-KEY': st.secrets["SERPER_API_KEY"],
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        results = response.json()
        # 提取前 3 筆搜尋結果摘要，直接餵給 AI
        snippets = [item['snippet'] for item in results.get('organic', [])[:3]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 執行主邏輯 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_term = st.text_input("搜尋", placeholder="例如: Holisoon, Carbatin...", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    
    with st.spinner(f"正在全自動同步雲端數據：{target}..."):
        # 第一步：獲取 Google 搜尋到的實時資料（解決 Holisoon 沒健保的問題）
        live_data = search_google_live(target)
        
        # 第二步：由 AI 根據抓到的實體資料進行精確整理
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        prompt = f"""你現在是藥學專家。根據以下從雲端搜尋到的實時資料片段，整理「{target}」的報告。
        ---
        實時搜尋資料：{live_data}
        ---
        【硬性要求】：
        1. 絕對禁止提供假設性數據或 XXXXX。
        2. 如果資料提及 Holisoon，請確保成分與台灣 TFDA 登記一致。
        3. 內容必須包含：正式品名、成分含量、許可證字號。
        4. 移除所有健保點數。標題用【 】，禁止粗體。
        
        格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 官方實時分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception:
            st.error("雲端引擎暫時繁忙。")

st.markdown("---")
st.caption("⚠️ 系統已啟動「自動轉向搜尋」功能，確保非健保藥品亦能獲取精確資料。")
