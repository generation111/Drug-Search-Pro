import streamlit as st
from openai import OpenAI
import requests
import json
import urllib.parse

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

# --- 2. 核心搜尋與健保自動對接邏輯 ---
def advanced_med_fetch(query):
    # 使用 Serper API 模擬手動 Google 搜尋，抓取官網與健保實體資訊
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"藥品 健保代碼 健保價格 官網 仿單 {query}",
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
        # 提取搜尋摘要，確保 AI 獲得實體資料片段
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:5]]
        return "\n".join(snippets)
    except:
        return "雲端連線異常，無法獲取實時數據。"

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

# 搜尋框
search_term = st.text_input("搜尋", placeholder="輸入藥名 (如: Sheco, Holisoon, Carbatin...)", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    
    with st.spinner(f"正在全自動同步雲端官方數據：{target}..."):
        # 第一步：執行 Google 實時抓取
        live_context = advanced_med_fetch(target)
        
        # 第二步：由 OpenAI 根據實體資料進行精確分析
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 強制指令：嚴禁誤判自費，必須尋找健保資料
        prompt = f"""你現在是資深藥務經理。請根據以下搜尋到的實時資訊，整理「{target}」的專業報告。
        ---
        搜尋實時摘要：{live_context}
        ---
        【核心要求】：
        1. 嚴禁在未經證實的情況下將藥品歸類為「自費」或「指示藥品」。
        2. 針對「Sheco」，必須確認其健保給付狀態，並尋找其健保代碼與價格。
        3. 針對「Holisoon」，必須對應其正確成分（如 Benzydamine HCl）與官方資訊，禁止使用假設數據。
        4. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保給付規定】、【藥師臨床提示】。
        5. 【健保給付規定】必須具體包含：健保代碼、健保價格及給付條件。若確實無給付，才可標註。
        
        回答規範：繁體中文、禁止粗體、標題統一使用【 】。
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # --- 4. 渲染置中報告 ---
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 臨床分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                else:
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"分析引擎調用失敗。")

st.markdown("---")
st.caption("⚠️ 本系統已改位置中佈局並優化健保邏輯。數據來源：TFDA / NHI / Google Search。")
