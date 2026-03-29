import streamlit as st
from openai import OpenAI
import time

# --- 1. 配置與樣式 ---
st.set_page_config(page_title="藥速知 Pro", layout="wide")

# 套用您的 React 科技感風格
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;700;900&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #07101e;
        color: #dde6f0;
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* 模仿 React 版的 Card 樣式 */
    .card {
        background: #0e1a2e;
        border: 1px solid rgba(79,156,249,0.14);
        border-radius: 18px;
        padding: 32px;
        margin-top: 20px;
        box-shadow: 0 20px 70px rgba(0,0,0,0.6);
    }
    
    .sec-header {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .sec-bar {
        width: 4px;
        height: 16px;
        background: #3b82f6;
        border-radius: 2px;
    }
    
    .sec-content {
        font-size: 15px;
        line-height: 1.8;
        color: #7a95b0;
        margin-bottom: 25px;
        white-space: pre-wrap;
    }
    
    /* 漸層標題 */
    .grad-text {
        background: linear-gradient(135deg, #60a5fa, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 初始化 OpenAI ---
def get_client():
    if "openai" in st.secrets:
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

client = get_client()

# --- 3. 核心邏輯 ---
def generate_report(drug):
    prompt = f"""你是一位資深臨床藥師。分析藥品「{drug}」。
    必須嚴格按以下結構回答，且不使用 Markdown 粗體語法：

    【藥品基本資料】
    成分、常見商品名、台灣健保代碼與點數。

    【臨床適應症與用法】
    TFDA適應症、用法用量、特殊族群調整。

    【健保給付規定】
    給付條件、開立限制、自費事項。

    【藥師臨床提示】
    交互作用、副作用、衛教重點。
    """
    
    response = client.chat.completions.create(
        model="gpt-4o", # 或使用您的 sk- 權限能用的模型
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# --- 4. UI 渲染 ---
st.markdown(f'<h1>藥事快搜 <span class="grad-text">Pro Edition</span></h1>', unsafe_allow_html=True)
st.caption("引用 TFDA 許可證 · 健保給付規範 · 臨床藥學資料庫")

# 快速標籤
tags = ["Metformin", "Amoxicillin", "Warfarin", "Atorvastatin"]
cols = st.columns(len(tags))
selected_tag = None
for i, tag in enumerate(tags):
    if cols[i].button(tag, use_container_width=True):
        selected_tag = tag

query = st.text_input("搜尋", value=selected_tag if selected_tag else "", placeholder="輸入藥名或成分...", label_visibility="collapsed")

if query:
    if not client:
        st.error("請先設定 OpenAI API Key")
    else:
        with st.spinner("正在查詢資料庫..."):
            try:
                result = generate_report(query)
                
                # 解析並顯示
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"<h2>{query} 臨床報告</h2>", unsafe_allow_html=True)
                
                sections = ["藥品基本資料", "臨床適應症與用法", "健保給付規定", "藥師臨床提示"]
                content = result
                
                for sec in sections:
                    marker = f"【{sec}】"
                    if marker in content:
                        # 簡單的切割邏輯
                        parts = content.split(marker)
                        if len(parts) > 1:
                            # 取得該段內容直到下一個標題
                            sub_content = parts[1].split("【")[0].strip()
                            st.markdown(f"""
                                <div class="sec-header"><div class="sec-bar"></div>{sec}</div>
                                <div class="sec-content">{sub_content}</div>
                            """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.caption("⚠️ 本工具提供臨床參考資訊，不取代正式藥典與醫師判斷")
                
            except Exception as e:
                st.error(f"查詢出錯：{e}")
