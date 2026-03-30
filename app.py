import streamlit as st
from openai import OpenAI
import requests
import json

# --- 1. UI 配置 (置中佈局 centered) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { 
        background: #0e1a2e; 
        border: 1px solid #3b82f6; 
        border-radius: 12px; 
        padding: 30px; 
        margin-top: 20px;
    }
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

# --- 2. 純粹雲端檢索函數 (不設人工映射) ---
def pure_cloud_fetch(query):
    # 直接模擬 Google 搜尋行為，不進行任何預設關鍵字替換
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"藥品 健保價格 健保代碼 官網 仿單 {query}",
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
        # 僅提取搜尋結果的摘要作為 AI 分析的依據
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:5]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主畫面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

# 單一搜尋入口
search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: chef, carbatin, holisoon...)", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在全自動同步雲端數據：{target}..."):
        # 執行純粹搜尋
        live_context = pure_cloud_fetch(target)
        
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 修正 Prompt：要求 AI 必須基於「搜尋結果」提供事實，禁止瞎掰或給出「待確認」
        prompt = f"""你現在是專業藥務經理。請分析藥品「{target}」。
        ---
        【搜尋參考資料】：
        {live_context}
        ---
        【硬性要求】：
        1. 僅根據參考資料與你的藥學知識庫進行分析。
        2. 嚴禁出現「待確認」、「未提供」或「XXXXX」。
        3. 必須包含：正確成分、規格、許可證字號。
        4. 【健保給付規定】必須對接真實的健保代碼與價格。若搜尋結果顯示為自費或指示藥，請如實標註。
        5. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        
        回答規範：繁體中文、禁止粗體、標題統一使用【 】。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 臨床分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                else:
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"分析引擎連線失敗。")

st.markdown("---")
st.caption("⚠️ 本系統已移除特定藥品對接邏輯，完全依賴即時雲端檢索。")
