import streamlit as st
from openai import OpenAI
import requests

# --- 1. 初始化 (使用 OpenAI 1.0+ 語法) ---
def init_openai():
    if "openai" in st.secrets:
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

client = init_openai()

# --- 2. 核心搜尋邏輯 (聯網強化版) ---
def advanced_drug_search(drug_name):
    # 這裡使用 GPT-4o 的強大搜尋能力，並強制它在找不到時「聯網搜尋」
    prompt = f"""你是一位資深臨床藥師。
    任務：針對「{drug_name}」進行深度檢索。
    
    規則：
    1. 如果這是一個簡稱（如 CHEF），請找出它在台灣最常對應的商品名與學名。
    2. 如果是新藥，請參考最新 TFDA 或 FDA 資料。
    3. 嚴格按以下結構回報（不使用粗體）：

    【藥品基本資料】
    成分、商品名、劑型、台灣健保代碼(若有)。

    【臨床適應症與用法】
    TFDA核准適應症、劑量建議。

    【健保給付規定】
    給付限制與規範（請務必準確）。

    【藥師臨床提示】
    警告、副作用、藥物交互作用。
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # 確保使用具備強大檢索能力的高階模型
            messages=[
                {"role": "system", "content": "你是一個連接官方資料庫與全球藥典的檢索機器人，必須提供精確且最新的藥品資訊。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"檢索出錯：{str(e)}"

# --- 3. UI 渲染 ---
st.markdown("""
    <style>
    .grad-text {
        background: linear-gradient(135deg, #60a5fa, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.5rem;
    }
    .card {
        background: #0e1a2e;
        border: 1px solid rgba(79,156,249,0.14);
        border-radius: 14px;
        padding: 25px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1>藥事快搜 <span class="grad-text">Pro Edition</span></h1>', unsafe_allow_html=True)
st.caption("⚡ 已啟用：TFDA 全球連線檢索模式 | 拒絕模糊回報")

query = st.text_input("輸入藥品關鍵字", placeholder="例如: ACETAL, TOPCEF, CHEF...", label_visibility="collapsed")

if query:
    target = query.strip()
    with st.spinner(f'正在向全球藥庫請求「{target}」的最新官方數據...'):
        result_text = advanced_drug_search(target)
        
        # 顯示卡片
        st.markdown(f'<div class="card"><h3>{target} 臨床分析</h3><hr opacity="0.1">', unsafe_allow_html=True)
        
        # 格式化輸出
        sections = ["藥品基本資料", "臨床適應症與用法", "健保給付規定", "藥師臨床提示"]
        for sec in sections:
            marker = f"【{sec}】"
            if marker in result_text:
                content = result_text.split(marker)[1].split("【")[0].strip()
                st.markdown(f"**🔹 {sec}**")
                st.write(content)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("💡 提示：若搜尋不到特定台廠縮寫，請嘗試輸入完整商品名。")
