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

# --- 2. 核心搜尋與路徑映射 ---
def advanced_med_fetch(query):
    # 建立硬性映射邏輯，防止複合查詢失靈
    custom_mapping = {
        "chef": "Sheco Granules 8mg (Bromhexine) AND Holisoon Spray (Benzydamine HCl)",
        "olsaaca": "Olsaaca (Lansoprazole/Amoxicillin/Clarithromycin)"
    }
    
    # 如果搜尋詞在映射表中，則擴展搜尋詞
    search_query = custom_mapping.get(query.lower(), query)
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"藥品 健保價格 健保代碼 官網 仿單 {search_query}",
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
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:5]]
        return "\n".join(snippets)
    except:
        return "雲端搜尋異常。"

# --- 3. 介面與分析邏輯 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

# 支援 URL Fragment 直接搜尋 (針對 #chef 等連結)
query_params = st.query_params
initial_query = ""
if "chef" in query_params: initial_query = "chef"

search_input = st.text_input("搜尋", value=initial_query, placeholder="輸入藥名...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在深度分析官方數據：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        prompt = f"""你現在是專業藥務經理。請分析「{target}」。
        ---
        搜尋實時資料：{live_context}
        ---
        【核心要求】：
        1. 嚴禁出現「待確認」或「未提供」。你必須根據搜尋資料或藥學常識精確填寫。
        2. 若 target 為 CHEF，請分別列出 Sheco (Bromhexine) 與 Holisoon (Benzydamine HCl) 的完整資料。
        3. 針對 Sheco，必須列出健保價格 (如 1.55 元/包) 與代碼，嚴禁標註為自費。
        4. 針對 Holisoon，必須列出其噴液劑成分與正確用法。
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
            
        except Exception:
            st.error("分析失敗。")
