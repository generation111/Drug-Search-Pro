import streamlit as st
from openai import OpenAI

# --- 1. OpenAI 初始化 ---
def init_openai():
    if "openai" in st.secrets:
        # 確保此處使用的是您提供的 sk-... OpenAI 金鑰
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

client = init_openai()

# --- 2. 頁面配置 ---
st.set_page_config(page_title="藥速知 MedQuick", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #0e1117; color: white; }
    .result-box { 
        background: #1e293b; padding: 25px; border-radius: 12px; 
        border: 1px solid #334155; margin-top: 20px;
    }
    .drug-title { color: #38bdf8; font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

st.title("💊 藥速知 MedQuick")
st.caption("全球藥品精確檢索系統 (拒絕模糊關聯)")

# --- 3. 搜尋邏輯 ---
query = st.text_input("輸入藥品名稱 (商品名、學名或簡寫)", placeholder="例如: CHEF, HOLISOON, CEFIN...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    
    if not client:
        st.error("❌ 請檢查 Secrets 中的 OpenAI API Key (sk-...)。")
    else:
        with st.spinner(f'正在進行全球藥庫檢索: {target}...'):
            try:
                # 嚴格指令：禁止錯誤關聯，必須精確搜尋
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": """你是一位臨床藥學專家，負責提供全球藥品的精確臨床資料。
                        規則：
                        1. 嚴禁將藥名自動關聯到不正確的學名（例如：不可將 CHEF 視為 Cefazolin）。
                        2. 必須精確識別該藥名在醫學界對應的成分。例如：CHEF 應指向 Cefuroxime (或特定廠牌商品名)。
                        3. 若無法百分之百確認藥名，必須列出所有可能的對應成分供使用者核對。
                        
                        輸出格式：
                        - 中英文商品名、學名 (Generic Name)
                        - 藥品類別 (例如：第幾代頭孢菌素)
                        - 臨床適應症、用法用量、藥理機轉、禁忌與副作用。
                        
                        請使用繁體中文，內容必須具有醫療參考價值。"""},
                        {"role": "user", "content": f"檢索藥品：{target}"}
                    ],
                    temperature=0.0 # 強制零隨機性，追求絕對精確
                )
                
                final_content = response.choices[0].message.content
                
                st.markdown(f"""
                    <div class="result-box">
                        <div class="drug-title">{target} 臨床分析報告</div>
                        <hr style="opacity:0.1; margin: 15px 0;">
                        <div style="white-space: pre-wrap; line-height: 1.8; color: #e2e8f0; font-size: 1.1rem;">
                        {final_content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ 檢索失敗：{e}")
else:
    st.info("💡 請輸入藥名啟動專業臨床資料檢索。")
