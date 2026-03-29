import streamlit as st
from openai import OpenAI
import time

# --- 1. OpenAI 初始化 ---
def init_ai():
    if "openai" in st.secrets:
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

client = init_ai()

# --- 2. 頁面配置 (純淨藥品查詢風格) ---
st.set_page_config(page_title="藥速知 MedQuick", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #0e1117; color: white; }
    .result-box { 
        background: #1e293b; padding: 25px; border-radius: 12px; 
        border-left: 5px solid #0ea5e9; margin-top: 20px;
    }
    .drug-header { color: #0ea5e9; font-size: 1.8rem; font-weight: 800; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("💊 藥速知 MedQuick")
st.markdown("---")

# --- 3. 搜尋邏輯 (移除所有資料庫干擾) ---
query = st.text_input("請輸入藥品商品名或成分名", placeholder="例如: CHEF, CEFIN, HOLISOON...", label_visibility="collapsed")
# 在 app.py 的搜尋邏輯中加入這段判斷
try:
    # ... 原本的 AI 請求代碼 ...
except Exception as e:
    if "401" in str(e):
        st.error("❌ API Key 格式錯誤！偵測到您可能填成了 Google API Key (AIza...)，請更換為 OpenAI 的 'sk-' 金鑰。")
    else:
        st.error(f"❌ 系統連線異常：{e}")

if query:
    target = query.strip().upper()
    
    # 建立即時顯示區塊
    with st.status(f"正在分析 {target} 臨床數據...", expanded=True) as status:
        if client:
            try:
                # 這裡直接呼叫 AI，不經過任何可能卡住的資料庫
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": """你是一位臨床藥師。請針對藥名提供精確臨床資料：
                        1. 學名 (Generic Name)
                        2. 臨床適應症 (Indication)
                        3. 用法用量 (Dosage)
                        4. 藥理作用機轉 (Mechanism of Action)
                        5. 禁忌與重要副作用。
                        請使用繁體中文，格式嚴謹。"""},
                        {"role": "user", "content": f"請提供藥品 {target} 的臨床藥理分析。"}
                    ],
                    temperature=0.2
                )
                final_content = response.choices[0].message.content
                status.update(label="檢索完成！", state="complete", expanded=False)
                
                # 渲染結果卡片
                st.markdown(f"""
                    <div class="result-box">
                        <div class="drug-header">{target} 臨床分析報告</div>
                        <div style="white-space: pre-wrap; line-height: 1.8; color: #e2e8f0; font-size: 1.1rem;">
                        {final_content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"AI 服務暫時無法回應: {e}")
        else:
            st.error("請在 Secrets 中設定 OpenAI API Key")
else:
    st.info("💡 請輸入藥名並按下 Enter 鍵啟動檢索。")
