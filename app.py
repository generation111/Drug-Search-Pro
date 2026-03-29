import streamlit as st
from openai import OpenAI
import datetime

# --- 1. 初始化 OpenAI 服務 (加入縮進保護) ---
def init_ai():
    client = None
    try:
        # 這裡必須縮進
        if "openai" in st.secrets:
            api_key = st.secrets["openai"]["api_key"]
            # 檢查是否誤填了 Google API Key (AIza...)
            if api_key.startswith("AIza"):
                st.error("❌ 偵測到 API Key 格式錯誤：您填入的是 Google Key (AIza...)，請更換為 OpenAI 的 'sk-' 開頭金鑰。")
                return None
            client = OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"⚠️ 初始化異常: {e}")
    return client

client = init_ai()

# --- 2. 專業臨床 UI 介面 ---
st.set_page_config(page_title="藥速知 MedQuick", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #0e1117; color: white; }
    .result-box { 
        background: #1e293b; padding: 25px; border-radius: 12px; 
        border-left: 5px solid #0ea5e9; margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💊 藥速知 MedQuick")
st.caption("專業藥品臨床仿單資料檢索")

# --- 3. 搜尋核心邏輯 ---
query = st.text_input("輸入藥名 (商品名或成分名)", placeholder="例如: CHEF, CEFIN, HOLISOON...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    
    if not client:
        st.warning("請先於 Secrets 設定正確的 OpenAI API Key (sk-...)")
    else:
        with st.spinner(f'正在調閱 {target} 臨床仿單數據...'):
            try:
                # 調用專業藥理模型
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "你是一位專業臨床藥師。請針對藥名提供精確臨床資料：1.學名 2.臨床適應症 3.用法用量 4.藥理作用機轉 5.重要禁忌與副作用。請使用繁體中文，格式嚴謹。"},
                        {"role": "user", "content": f"分析藥品：{target}"}
                    ],
                    temperature=0.2
                )
                final_content = response.choices[0].message.content
                
                # 渲染結果
                st.markdown(f"""
                    <div class="result-box">
                        <h2 style="color:#38bdf8;">{target} 臨床分析報告</h2>
                        <hr style="opacity:0.1;">
                        <div style="white-space: pre-wrap; line-height: 1.8; color: #e2e8f0; font-size: 1.1rem;">
                        {final_content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                if "401" in str(e):
                    st.error("❌ API Key 無效。請確認您的 OpenAI Key 是否過期或餘額不足。")
                else:
                    st.error(f"❌ 檢索失敗：{e}")
else:
    st.info("💡 請輸入藥名並按下 Enter。")
