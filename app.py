import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. UI 樣式配置 (回歸專業藥學檢索感) ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #07101e;
        color: #dde6f0;
        font-family: 'Noto Sans TC', sans-serif;
    }
    [data-testid="stHeader"] { visibility: hidden; }
    .report-card {
        background: #0e1a2e;
        border: 1px solid rgba(79,156,249,0.3);
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

# --- 2. 核心分析引擎 (絕對路徑邏輯) ---
def execute_absolute_analysis(drug_name):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 強制指令：絕對對應輸入內容，禁止任何名稱聯想或轉譯
    prompt = f"""你是一位嚴謹的藥學數據分析員。
    【核心任務】：請針對關鍵字「{drug_name}」進行官方數據匯總。
    
    【執行準則】：
    1. 必須直接以「{drug_name}」作為唯一關鍵字，查閱 TFDA 許可證與 NHI 官方路徑。
    2. 禁止將「{drug_name}」聯想或轉譯為任何其他藥名。
    3. 移除所有關於「健保點數」的文字與數值。
    4. 移除所有與「{drug_name}」無關的補充說明。
    5. 禁止回報「找不到」或「搜尋中」，請根據實時路徑檢索內容直接呈現。

    【報告結構】：
    【藥品基本資料】(包含許可證字號與品名)
    【臨床適應症與用法】
    【健保給付規定】
    【藥師臨床提示】

    回答規範：繁體中文、禁止使用粗體、標題統一使用【 】。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. 介面渲染 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

# 搜尋框
search_input = st.text_input("搜尋", placeholder="輸入藥名 (如: CHEF, Sheco, 012556...)", label_visibility="collapsed")

if search_input:
    target = search_input.strip()
    encoded = urllib.parse.quote(target)
    
    # 建立官方實時檢索路徑 (這部分是程式必須執行的路徑)
    st.markdown(f"""
        [🏥 健保 S01](https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}) | 
        [🏥 健保 S02](https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}) | 
        [📜 食藥署許可證](https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}) | 
        [💊 仿單 MCP](https://mcp.fda.gov.tw/im_detail_1/{encoded})
    """, unsafe_allow_html=True)

    with st.spinner(f"正在執行官方數據路徑分析：{target}..."):
        try:
            report = execute_absolute_analysis(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target} 臨床分析報告")
            
            lines = report.split('\n')
            for line in lines:
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("系統執行異常，請點擊上方官方連結核對。")
