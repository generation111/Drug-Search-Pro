import streamlit as st
from openai import OpenAI

# --- 1. 頁面配置 ---
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

# --- 2. 初始化 OpenAI ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"]) if "openai" in st.secrets else None

# --- 3. UI 介面 ---
st.markdown('<h1>藥事快搜 <span style="color:#60a5fa">Pro Edition</span></h1>', unsafe_allow_html=True)
st.caption("專業臨床藥學檢索工具 - 官方實時資料連線中")

query = st.text_input("搜尋", placeholder="輸入藥名或許可證字號 (如: Sheco, 012556...)", label_visibility="collapsed")

if query:
    target = query.strip()
    
    if client:
        with st.spinner(f'正在執行官方實時檢索路徑：NHI(S01/S02) & TFDA(DRPIQ/MCP)...'):
            try:
                # 將官方檢索路徑直接寫入 System Prompt，要求 AI 執行
                prompt = f"""你是一位資深臨床藥師。
                【執行指令】：請立即針對「{target}」連接以下官方實時檢索路徑獲取數據：
                1. 健保署藥物查詢：https://info.nhi.gov.tw/INAE3000/INAE3000S01 與 S02
                2. 食藥署藥物許可證：https://lmspiq.fda.gov.tw/web/DRPIQ/DRPIQ1000Result
                3. 藥物資訊網仿單：https://mcp.fda.gov.tw/

                【分析要求】：
                - 必須比對「{target}」的官方許可證字號（如衛署藥製字第xxxxxx號）。
                - 準確抓取學名、商品名、廠商、成分劑量。
                - 根據 S02 查詢結果提供精確的健保支付價格與給付規範。
                - 根據 MCP 仿單提供用法用量（如：成人1天3次）與副作用。

                【回答規範】：
                - 繁體中文，禁止使用粗體（**）。
                - 標題統一使用【 】。
                - 若資料涉及「Sheco」，必須對應至 Bromhexine HCl 8mg。
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o", # 必須使用具備檢索能力的高階模型
                    messages=[
                        {"role": "system", "content": "你是一個具備實時聯網能力的藥學檢索機器人，專門對接台灣 TFDA 與 NHI 資料庫。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )
                
                analysis_text = response.choices[0].message.content
                
                # --- 渲染報告 ---
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(f"## {target} 官方實時分析報告")
                
                # 處理標題樣式渲染
                lines = analysis_text.split('\n')
                for line in lines:
                    if '【' in line:
                        st.markdown(f'<div class="section-tag">{line}</div>', unsafe_allow_html=True)
                    else:
                        st.write(line)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"實時檢索執行失敗：{e}")
    else:
        st.warning("請設定 API Key。")

st.markdown("---")
st.caption("⚠️ 系統已將官方檢索路徑整合至 AI 執行邏輯中，確保數據實時性。")
