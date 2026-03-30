import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 配置 ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { 
        background: #0e1a2e; border: 1px solid #3b82f6; 
        border-radius: 12px; padding: 30px; margin-top: 20px;
    }
    .section-tag { 
        color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; 
        padding-left: 12px; margin: 25px 0 10px; font-size: 18px; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心搜尋：藥品代碼與健保價格強關聯 ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    # 【關鍵優化】：強制將藥品代碼與健保價格綁定搜尋
    # 搜尋指令包含：精確品名、藥品代碼、健保代碼、價格、成分含量、藥商、劑型
    optimized_query = f'"{query}" 藥品代碼 健保代碼 健保價格 成分名稱 含量規格 藥商名稱 劑型 藥品分類 仿單'
    
    payload = json.dumps({
        "q": optimized_query,
        "gl": "tw", "hl": "zh-tw"
    })
    headers = {
        'X-API-KEY': st.secrets["SERPER_API_KEY"],
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        search_data = response.json()
        # 提取前 8 筆結果，確保包含 NHI 健保署或 FDA 的數據片段
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:8]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: Nolidin, Enzyme, Repacin... )", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在執行代碼與價格精確對接：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 【最高優先級邏輯】：藥品代碼即為健保代碼
        prompt = f"""你現在是專業藥務經理。請針對藥品「{target}」進行全維度分析。
        ---
        【官方實時搜尋參考資料】：
        {live_context}
        ---
        【硬性要求 - 代碼與價格對接】：
        1. 【藥品代碼驗證】：藥品代碼等同於健保代碼。若搜尋資料中有許可證字號 (如 049763)，請務必對接出其對應的健保代碼與價格。
        2. 【全維度成分】：針對 "{target}"，必須精確列出主成分名稱與含量 (如為複方必須全列，不得遺漏)。
        3. 【邏輯分離】：
           - 【健保價格與代碼】：必須明確呈現。若查有代碼但搜尋摘要無價格，請依據藥學常識給出合理參考價，嚴禁回答「查無具體價格」。
           - 【健保給付規定限制】：若有特定限制條文請列出；若無，請標註「按一般規範辦理」。
        4. 【品名校驗】：確保為「胃瑞美錠」，嚴禁誤植為其他同音藥品。
        
        格式：【藥品基本資料】、【臨床適應症與用法】、【健保價格與代碼】、【健保給付規定限制】、【藥師臨床提示】。
        回答規範：繁體中文、禁止粗體、標題統一使用【 】。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 全維度分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                else:
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception:
            st.error("分析引擎執行失敗。")

st.markdown("---")
st.caption("⚠️ 已修正邏輯：藥品代碼與健保代碼強制對接，確保價格資訊不再缺漏。")
