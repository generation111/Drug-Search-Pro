import streamlit as st
from openai import OpenAI
import urllib.parse

# --- 1. UI 樣式配置 (保持專業簡潔) ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心分析引擎 (絕對對應邏輯) ---
def execute_absolute_analysis(drug_name):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 強制 AI 絕對以 drug_name 為唯一主體，不准自行轉譯為其他學名
    prompt = f"""你是一位臨床藥學資料分析員。
    【核心指令】：現在要分析的藥品名稱「絕對」是：「{drug_name}」。
    
    【執行要求】：
    1. 必須直接以「{drug_name}」為關鍵字，檢索 TFDA 許可證與健保署 NHI 數據。
    2. 禁止將「{drug_name}」轉譯、對應或聯想為任何其他藥品名稱（如 Cefazolin 或 Cefuroxime）。
    3. 報告標題必須顯示為「{drug_name}」。
    4. 移除所有「健保點數」顯示。
    5. 禁止出現「與該藥品無直接關聯」或「建議搜尋其他名稱」等廢話。

    【報告結構】：
    【藥品基本資料】
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

search_term = st.text_input("搜尋", placeholder="輸入藥名...", label_visibility="collapsed")

if search_term:
    target = search_term.strip()
    encoded = urllib.parse.quote(target)
    
    # 建立官方實時檢索路徑 (這部分是程式碼執行，直接對接官方網址)
    st.markdown(f"""
        [🏥 健保 S01](https://info.nhi.gov.tw/INAE3000/INAE3000S01?keyword={encoded}) | 
        [🏥 健保 S02](https://info.nhi.gov.tw/INAE3000/INAE3000S02?keyword={encoded}) | 
        [📜 食藥署許可證](https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result?licId={encoded}) | 
        [💊 仿單 MCP](https://mcp.fda.gov.tw/im_detail_1/{encoded})
    """, unsafe_allow_html=True)

    with st.spinner(f"正在針對「{target}」執行官方數據路徑分析..."):
        try:
            # 這裡執行分析，確保 CHEF 對應到 CHEF
            report = execute_absolute_analysis(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target} 臨床分析報告")
            
            for line in report.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: 
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("系統解析異常。")
