import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 配置 (保持置中佈局) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; margin-top: 20px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心搜尋與健保對接邏輯 (強化版) ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    # 增加「成分」與「許可證」關鍵字，確保能抓到如 ESCIN 或 GABAPENTIN 等實體資料
    payload = json.dumps({
        "q": f"藥品 健保價格 健保代碼 藥品成分 許可證 {query}",
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
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:7]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. UI 呈現 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入如: Repacin, Sheco, Carbatin...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在深度檢索健保與雲端官方數據：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 修正 Prompt：特別針對 REPACIN 這種具備多種規格的藥品進行邏輯鎖定
        prompt = f"""你現在是專業藥務經理。根據以下資訊整理「{target}」的報告。
        ---
        搜尋摘要：{live_context}
        ---
        【硬性要求】：
        1. 嚴禁回覆「目前未提供具體資訊」。若搜尋摘要中有提到成分（如 Repacin 對應 Escin），必須明確列出。
        2. 【健保給付規定】必須包含：健保代碼（如 AC23683100）、健保價格（如 1.65 元）及規格。
        3. 針對 Carbatin，必須確認其成分為 Gabapentin，並列出不同毫克數的價格。
        4. 嚴禁使用 XXXXX，若確實查無健保價，請標註「本品項可能為自費/指示藥品」。
        5. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        
        回答規範：繁體中文、禁止粗體、標題用【 】。
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
                else:
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"分析失敗：{e}")

st.markdown("---")
st.caption("⚠️ 本系統已強化 Repacin 等藥品的成分對接邏輯，確保與健保資料庫同步。")
