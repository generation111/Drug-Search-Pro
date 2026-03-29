import streamlit as st
from openai import OpenAI

# --- 1. 專業 UI 配置 ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 25px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 建立專家對照字典 (防止 AI 亂猜) ---
EXPERT_MAPPING = {
    "RELAX": "Mephenoxalone (Mocolax) 200mg",
    "SHECO": "Bromhexine HCl 8mg (捨咳顆粒)",
    "CHEF": "Cefuroxime Axetil 250mg",
    "TOPCEF": "Cephradine"
}

# --- 3. 分析引擎 ---
def drug_analysis_engine(query_term):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 檢查是否有預設的對照資訊
    search_target = EXPERT_MAPPING.get(query_term.upper(), query_term)
    
    prompt = f"""你是一位精確的臨床藥師。
    【搜尋目標】：{search_target}
    
    【執行指令】：
    1. 檢索 TFDA 許可證資料與 NHI 健保給付規範。
    2. 如果目標是 RELAX，必須對應到骨骼肌肉鬆弛劑 Mephenoxalone。
    3. 如果目標是 Sheco，必須對應到 Bromhexine HCl 8mg。
    4. 嚴格禁止出現 Tigecycline 除非使用者明確搜尋該藥。
    5. 移除所有「健保點數」資訊。

    【報告結構】：
    【藥品基本資料】
    【臨床適應症與用法】
    【健保給付規定】
    【藥師臨床提示】

    回答規範：繁體中文、不使用粗體、標題統一使用【 】。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 4. 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋藥名", placeholder="例如: RELAX, Sheco...", label_visibility="collapsed")

if query:
    target = query.strip()
    with st.spinner(f"正在對接官方實時數據分析 {target}..."):
        try:
            result = drug_analysis_engine(target)
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {target.upper()} 臨床分析報告")
            
            lines = result.split('\n')
            for line in lines:
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                elif "點" not in line: # 二次過濾點數資訊
                    st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error("系統繁忙中，請稍後再試。")
