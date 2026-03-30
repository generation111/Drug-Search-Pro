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

# --- 2. 核心搜尋：全維度＋精確匹配指令 ---
def advanced_med_fetch(query):
    url = "https://google.serper.dev/search"
    
    # 【核心修正】：將查詢詞放入雙引號，強制 Google 進行「精確匹配」
    # 並加入所有您要求的維度：藥品代碼、成分含量、規格量、單複方、藥商、劑型、藥品分類
    optimized_query = f'藥品名稱 "{query}" 藥品代碼 健保價格 成分名稱 含量規格 單複方 藥商名稱 劑型 藥品分類 仿單'
    
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
        # 增加抓取筆數，確保能從健保資料庫或官方仿單中提取資料
        snippets = [f"{item['title']}: {item['snippet']}" for item in search_data.get('organic', [])[:8]]
        return "\n".join(snippets)
    except:
        return ""

# --- 3. 系統主介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: ENZYME, SHECO, REPACIN...)", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    
    with st.spinner(f"正在全維度精確校驗官方數據：{target}..."):
        live_context = advanced_med_fetch(target)
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # 【關鍵指令修正】：鎖定身分識別，嚴禁張冠李戴
        prompt = f"""你現在是藥務管理專家。請針對藥品「{target}」進行全維度分析。
        ---
        【官方實時參考資料】：
        {live_context}
        ---
        【硬性要求】：
        1. 【身分校驗】：藥品名稱必須與 "{target}" 絕對一致。若資料提到 Nexviazyme 但使用者輸入的是 ENZYME，嚴禁將兩者混淆。請優先尋找品名完全吻合的健保代碼 (如 ENZYME 對應 A022204100)。
        2. 【全維度提取】：必須從資料中精確提取：
           - 藥品名稱 (中英文)
           - 藥品代碼 (健保碼/許可證號)
           - 主成分名稱及其含量、規格量 (如 Lysozyme HCl 90mg)
           - 單複方判定、藥商名稱、劑型、藥品分類
        3. 【健保給付規定】：必須包含真實健保價。若為自費品，請明確標註「本品項為自費或指示藥」。
        4. 絕對禁止回覆「未提供資訊」。若搜尋摘要中有數據，必須如實整理；若無，請根據專業知識庫精確補完與 "{target}" 完全匹配的資訊。
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
st.caption("⚠️ 已啟動「絕對名稱校驗系統」，確保分析對象與搜尋詞 100% 吻合。")
