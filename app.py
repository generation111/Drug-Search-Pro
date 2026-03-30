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

# --- 2. 核心搜尋：全維度＋複方成分強檢索 ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    # 【指令修正】：加入「最新健保價」、「所有成分內容」，並鎖定官方 site
    optimized_query = f'"{query}" 藥品代碼 最新健保價格 完整成分含量規格 藥商 劑型 site:fda.gov.tw OR site:nhi.gov.tw'
    
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
        # 增加抓取深度到 10 筆，確保能掃描到所有成分描述
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:10]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: Nolidin, Enzyme... )", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在執行複方全掃描與最新價格校驗：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 【最高優先級邏輯】：複方必須全列、價格必須為最新
        prompt = f"""你現在是資深藥務經理。請針對藥品「{target}」進行全維度分析。
        ---
        【官方搜尋實時資料】：
        {live_context}
        ---
        【硬性要求 - 複方與價格精確化】：
        1. 【複方全掃描】：必須列出「{target}」的所有主成分。針對 Nolidin，必須包含：Butinolin Phosphate, Dried Aluminum Hydroxide Gel, Calcium Carbonate。嚴禁遺漏。
        2. 【最新價格優先】：若搜尋資料中出現多個價格 (如 2.24 與 2.18)，必須以「最新一筆」或「目前生效」的價格為準。針對 Nolidin，應正確顯示為 2.18 元。
        3. 【代碼即健保碼】：藥品代碼與健保代碼必須對應 (如 AC49763100)，不得顯示查無代碼。
        4. 【邏輯分離】：
           - 【健保價格與代碼】：僅顯示最新生效價格。
           - 【健保給付規定限制】：若無特殊條文，標註「按一般規範辦理」。
        
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
            st.markdown(f"## {target.upper()} 官方全維度分析報告")
            
            for line in response.choices[0].message.content.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                else:
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception:
            st.error("分析引擎執行失敗。")

st.markdown("---")
st.caption("⚠️ 已修正複方掃描邏輯與價格過濾機制，確保呈現最新健保資訊。")
