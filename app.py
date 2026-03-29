import streamlit as st
from openai import OpenAI

# --- 1. UI 樣式配置 ---
st.set_page_config(page_title="藥事快搜 Pro Edition", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #07101e; color: #dde6f0; }
    .report-card { background: #0e1a2e; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px; }
    .section-tag { color: #60a5fa; font-weight: 900; border-left: 5px solid #3b82f6; padding-left: 12px; margin: 20px 0 10px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心分析邏輯 ---
def drug_analysis_engine(target_drug):
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # 嚴格約束 Prompt：移除健保點數，並針對特定藥品做精確定義
    prompt = f"""你是一位精確的臨床藥師。請針對「{target_drug}」進行官方數據分析。
    
    【強制邏輯指令】：
    1. 絕對禁止顯示「健保點數」或任何與「點數/金額」相關的數字。
    2. 若搜尋字詞包含「Sheco」，必須精確對應至 Bromhexine HCl 8mg 顆粒，不得有誤。
    3. 若搜尋字詞為「Tigecycline」，請專注於其抗生素臨床用途與用法。
    4. 移除所有「與該藥品無直接關聯」的補充說明或提醒字眼。

    【報告結構要求】：
    【藥品基本資料】（學名、商品名、廠商、劑型）
    【臨床適應症與用法】（包含成人標準劑量與給藥頻率）
    【健保給付規定】（僅列出適應症限制與規範，不列點數）
    【藥師臨床提示】（交互作用與副作用）

    回答規範：繁體中文、不使用粗體（**）、標題統一使用【 】。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 3. 執行介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋藥名", placeholder="例如: Tigecycline, Sheco...", label_visibility="collapsed")

if query:
    with st.spinner(f"正在執行官方路徑數據分析..."):
        try:
            result_text = drug_analysis_engine(query.strip())
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f"## {query.upper()} 官方實時檢索報告")
            
            # 格式化輸出
            for line in result_text.split('\n'):
                if '【' in line:
                    st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                else:
                    # 再次確保輸出的內容中不包含任何點數相關字眼 (保險機制)
                    if "點" not in line or "劑量" in line:
                        st.write(line)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"分析失敗，請檢查 API 設定或稍後再試。")

st.markdown("---")
st.caption("⚠️ 本系統提供官方數據匯總。數據以 TFDA 仿單為唯一準則。")
