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
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; margin-top: 20px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 遞進式搜尋邏輯 ---
def deep_med_fetch(query):
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # 第一輪：全維度搜尋
    q1 = f'"{query}" 藥品代碼 健保價格 成分含量 site:nhi.gov.tw OR site:fda.gov.tw'
    # 第二輪：針對通用詞優化 (排除生物定義，鎖定健保品項)
    q2 = f'"{query}" 健保用藥品項網路查詢服務 價格 廠商'
    
    combined_results = []
    for q in [q1, q2]:
        payload = json.dumps({"q": q, "gl": "tw", "hl": "zh-tw"})
        try:
            res = requests.post(url, headers=headers, data=payload).json()
            combined_results.extend([f"{i['title']}: {i['snippet']}" for i in res.get('organic', [])[:5]])
        except: continue
        
    return "\n".join(combined_results)

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: ENZYME, REPACIN...)", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在全維度穿透檢索官方數據：{target}..."):
        live_context = deep_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 【最高指令修正】：針對 ENZYME 等品名強化校驗
        prompt = f"""你現在是藥務經理。請分析藥品「{target}」。
        ---
        【參考資料】：
        {live_context}
        ---
        【硬性要求】：
        1. 【品名校驗】：藥品名稱必須與 "{target}" 100% 吻合。針對「ENZYME」，應對應為消炎酵素錠 (如 Lysozyme 90mg)，嚴禁套用 Nolidin 或 Nexviazyme 的成分。
        2. 【代碼即價格】：藥品代碼 = 健保代碼。若搜尋到代碼 (如 A022204100)，必須顯示對應價格。
        3. 【複方全掃描】：若是複方請全列；若是單方 (如 ENZYME 常見為單方 Lysozyme) 則明確標註。
        4. 【邏輯分離】：
           - 【健保價格與代碼】：必須顯示最新數據。
           - 【健保給付規定限制】：若無特定條文，請標註「按一般規範辦理」。
        
        格式：【藥品基本資料】、【臨床適應症與用法】、【健保價格與代碼】、【健保給付規定限制】、【藥師臨床提示】。
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
st.caption("⚠️ 已啟動遞進式搜尋：針對通用藥名強化健保資料庫穿透力。")
