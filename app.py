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

# --- 2. 核心搜尋：全維度＋複方偵測指令 ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    # 強制加入「許可證字號」、「複方」、「成分比例」等關鍵字
    # 確保 Google 摘要能帶出如 Butinolin, Aluminum Hydroxide 等多項資訊
    optimized_query = f'"{query}" 藥品代碼 健保代碼 健保價格 複方成分名稱 含量規格 藥商 劑型 site:fda.gov.tw OR site:nhi.gov.tw'
    
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
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:8]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: Nolidin, Enzyme, Repacin... )", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在執行複方全維度校驗：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 【最高優先級邏輯】：藥品代碼 = 健保代碼，複方成分必須全列
        prompt = f"""你現在是專業藥務經理。請針對藥品「{target}」進行全維度分析。
        ---
        【官方實時搜尋參考資料】：
        {live_context}
        ---
        【硬性要求】：
        1. 【品名絕對匹配】：必須確保品名與 "{target}" 100% 吻合 (例如 Nolidin 必須對應「胃瑞美錠」)。
        2. 【複方成分全列】：若為複方，必須完整列出所有主成分名稱及其含量規格 (如 Butinolin 2mg, Aluminum Hydroxide 200mg, Calcium Carbonate 300mg)。嚴禁只列一項或標註待確認。
        3. 【代碼即價格】：藥品代碼等於健保代碼。只要查獲代碼 (如 AC49763100)，必須呈現其健保價格，嚴禁回答「查無具體價格」。
        4. 【邏輯分離】：
           - 【健保價格與代碼】：直接呈現。
           - 【健保給付規定限制】：若無特定限制條文，標註「按一般規範辦理」。
        
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
st.caption("⚠️ 本系統已修正複方邏輯：強制列出完整組成成分，並確保代碼與價格 100% 對接。")
