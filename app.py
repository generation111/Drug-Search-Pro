import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 配置 (置中佈局) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; margin-top: 20px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心搜尋：全維度指令優化 (關鍵修正處) ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    
    # 強制加入您要求的關鍵字維度：代碼、成分含量、規格量、單複方、藥商、劑型、分類
    # 這樣 Google 摘要就會優先顯示包含這些資訊的網頁片段 (如健保署、藥品百科)
    optimized_query = f"{query} 藥品代碼 健保價格 成分名稱 含量規格 單複方 藥商名稱 劑型 藥品分類 仿單"
    
    payload = json.dumps({
        "q": optimized_query,
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
        # 增加抓取深度至 8 筆，確保涵蓋官方與民間資料庫
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:8]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入如: Nolidin, Repacin, Sheco...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在全維度檢索官方數據：{target}..."):
        # 執行優化後的深度搜尋
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 修正 Prompt：嚴禁出現「未提供資訊」，要求 AI 強制解析搜尋摘要中的全維度數據
        prompt = f"""你現在是專業藥務經理。請針對藥品「{target}」進行全維度分析。
        ---
        【搜尋參考資料 (含代碼、成分、規格、藥商等)】：
        {live_context}
        ---
        【硬性要求】：
        1. 絕對禁止回覆「未提供具體成分資訊」。你必須從參考資料中提取：
           - 藥品名稱 (中英文)
           - 藥品代碼 (健保/許可證字號)
           - 主成分及其含量、規格量
           - 單複方判定、劑型、藥商名稱、藥品分類
        2. 【健保給付規定】必須包含真實的健保價格。若為自費品，請明確標註「本品項為自費或指示藥」。
        3. 針對 Nolidin, Repacin 等藥品，必須正確對應其藥理成分 (如 Bromhexine, Escin)。
        4. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        
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
            
        except Exception as e:
            st.error(f"分析失敗：{e}")

st.markdown("---")
st.caption("⚠️ 本系統已全面優化搜尋指令，強制檢索代碼、成分、規格、劑型等核心數據。")
