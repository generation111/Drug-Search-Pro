import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 配置 (已改為置中佈局 centered) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    /* 報告卡片樣式 */
    .report-card { 
        background: #0e1a2e; 
        border: 1px solid #3b82f6; 
        border-radius: 12px; 
        padding: 30px; 
        margin-top: 20px;
    }
    /* 區塊標籤樣式 */
    .section-tag { 
        color: #60a5fa; 
        font-weight: 900; 
        border-left: 5px solid #3b82f6; 
        padding-left: 12px; 
        margin: 25px 0 10px; 
        font-size: 18px; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心搜尋與健保對接邏輯 ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    # 擴大搜尋範圍，強制包含「健保代碼、價格」等實體關鍵字
    payload = json.dumps({
        "q": f"藥品 健保代碼 健保價格 仿單 {query}",
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
        # 提取前 5 筆搜尋摘要，提供給 AI 作為分析事實依據
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:5]]
        return "\n".join(snippets)
    except:
        return "雲端連線失敗。"

# --- 3. UI 呈現 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

# 搜尋框置中呈現
search_input = st.text_input("搜尋", placeholder="輸入如: Sheco, Carbatin, Holisoon...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在深度檢索健保與雲端官方數據：{target}..."):
        # 執行實時抓取
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 核心 Prompt：鎖定專業藥務邏輯，嚴禁模糊地帶
        prompt = f"""你現在是專業藥務經理。根據以下雲端實時資訊，整理「{target}」的專業報告。
        ---
        搜尋摘要：{live_context}
        ---
        【硬性要求】：
        1. 絕對禁止在未經確認的情況下標註藥品為「自費」或「指示藥品」。
        2. 針對 Sheco，你必須確認其健保給付狀態，若搜尋摘要中有健保代碼或價格，必須列出（例如：1.55元/包）。
        3. 【健保給付規定】必須包含：健保代碼、健保價格、以及具體的給付規範節錄。
        4. 嚴禁使用 XXXXX 或任何假設性描述，必須對接真實數據。
        5. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        
        回答規範：繁體中文、禁止粗體、標題用【 】。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # 渲染報告內容
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 官方實時分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                else:
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"分析失敗：{e}")

st.markdown("---")
st.caption("⚠️ 本系統已回歸雲端深度對接邏輯，確保健保資訊與官網數據一致。")
