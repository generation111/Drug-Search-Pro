import streamlit as st
import google.generativeai as genai

# --- 1. 初始化引擎 ---
def init_engine():
    if "openai" in st.secrets:
        api_key = st.secrets["openai"]["api_key"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-pro') # 使用更聰明的 Pro 版本
    return None

model = init_engine()

# --- 2. 專業 UI ---
st.set_page_config(page_title="藥速知 MedQuick", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #0e1117; color: white; }
    .result-box { background: #1e293b; padding: 25px; border-radius: 12px; border-left: 5px solid #10b981; }
    </style>
""", unsafe_allow_html=True)

st.title("💊 藥速知 MedQuick")

# --- 3. 核心檢索邏輯 (強化推論能力) ---
query = st.text_input("輸入藥名", placeholder="請輸入藥名 (例如: CHEF, CEFIN)...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    with st.spinner(f'正在進行臨床數據建模: {target}...'):
        try:
            # 關鍵：加入「台灣醫藥背景」與「簡稱推論」指令
            prompt = f"""你是一位資深的臨床藥師。
            使用者輸入的藥名是「{target}」。
            
            任務指令：
            1. 如果這是一個簡稱（例如 CHEF 指的是 Cefazolin），請直接以該學名進行分析。
            2. 如果是特定廠牌（如慈榛驊或其他代理商），請說明其商品特性。
            3. 必須輸出以下結構：
               - 中英文商品名與【學名 (Generic Name)】
               - 臨床適應症 (Indication)
               - 用法用量 (Dosage)
               - 藥理作用機轉 (Mechanism of Action)
               - 重要禁忌與副作用
            
            請使用繁體中文，語氣需專業且精確。"""
            
            response = model.generate_content(prompt)
            
            st.markdown(f"""
                <div class="result-box">
                    <h2 style="color:#10b981;">{target} 專家檢索報告</h2>
                    <hr style="opacity:0.1;">
                    <div style="white-space: pre-wrap; line-height: 1.8; color: #e2e8f0; font-size: 1.1rem;">
                    {response.text}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"檢索發生錯誤：{e}")
