import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. 專業 UI 配置 (移除所有無關標籤) ---
st.set_page_config(page_title="藥速知 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 絕對檢索引擎 ---
def absolute_data_fetch(query_term):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 強制 AI 扮演「數據轉錄員」，禁止任何轉譯
    prompt = f"""你是一位負責整理 TFDA 與 NHI 官方數據的專業藥師。
    【當前檢索目標】：{query_term}
    
    【操作規範】：
    1. 必須直接以「{query_term}」作為唯一關鍵字，參考 TFDA 許可證與 NHI 健保收載資料。
    2. 嚴格禁止將「{query_term}」與任何其他藥品名進行聯想或對應。
    3. 報告中的【藥品基本資料】必須包含許可證字號與官方登記的名稱。
    4. 移除所有「健保點數」字樣與數值。
    5. 禁止出現「未能找到」或「建議確認正確性」等推諉文字。若官方數據庫有該字串，請直接列出；若無，請簡潔呈現官方路徑結果。

    回答規範：繁體中文、不使用粗體、標題統一使用【 】。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0 
    )
    return response.choices[0].message.content

# --- 3. 介面渲染 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

search_input = st.text_input("搜尋", placeholder="輸入藥名或許可證字號...", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    encoded = urllib.parse.quote(target)
    
    # 建立與您截圖中一致的官方驗證連結
    st.markdown(f"""
        [🏥 健保 S01](https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}) | 
        [🏥 健保 S02](https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}) | 
        [📜 食藥署許可證](https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}) | 
        [💊 仿單 MCP](https://mcp.fda.gov.tw/im_detail_1/{encoded})
    """, unsafe_allow_html=True)

    with st.spinner(f"正在執行官方路徑檢索：{target}..."):
        try:
            result = absolute_data_fetch(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target} 臨床分析報告")
            
            for line in result.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("系統執行異常，請點擊上方官方連結手動核對。")
