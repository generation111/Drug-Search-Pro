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

# --- 2. 全維度搜尋函數 ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    # 加入精確匹配與全維度關鍵字
    optimized_query = f'藥品名稱 "{query}" 藥品代碼 健保價格 成分名稱 含量規格 劑型 藥商名稱 藥品分類 健保給付規定 仿單'
    
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
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:8]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: ENZYME, REPACIN, SHECO...)", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在執行全維度數據分離檢索：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 【核心邏輯修正】：分離「價格」與「規定」
        prompt = f"""你現在是專業藥務經理。請針對藥品「{target}」進行全維度分析。
        ---
        【官方參考資料】：
        {live_context}
        ---
        【硬性要求 - 邏輯分離原則】：
        1. 【藥品基本資料】：品名必須 100% 吻合 "{target}"。包含代碼、成分含量(如 Lysozyme 90mg)、規格量、藥商、劑型、藥品分類。
        2. 【價格與給付】：
           - 必須列出「健保價格」與「健保代碼」。
           - 若有價格但無「特定給付規定限制」，請標註「本品項依健保收載規定給付」。
           - 嚴禁因為找不到「給付規定」就判定為自費。只有在完全查無健保代碼時，才可標註為自費或指示藥。
        3. 【給付規定內容】：僅列出針對該成分或品項的特定限制條文（例如限制科別、限制診斷）。若無特定限制，則填寫「無特殊限制，按健保一般規範辦理」。
        4. 格式：【藥品基本資料】、【臨床適應症與用法】、【健保價格與代碼】、【健保給付規定限制】、【藥師臨床提示】。
        
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
            st.error("分析引擎調用失敗。")

st.markdown("---")
st.caption("⚠️ 已修正給付邏輯：分離「健保價格」與「給付規定」，確保分析不張冠李戴。")
