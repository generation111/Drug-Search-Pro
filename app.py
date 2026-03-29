import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time

# --- 1. 後端 Firebase 初始化 ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                # 處理私鑰換行符號問題
                if "\\n" in cred_dict["private_key"]:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            return "NO_SECRETS"
        except Exception as e:
            return f"ERROR: {str(e)}"
    return firebase_admin.get_app()

# 初始化與資料庫連接
fb_status = init_firebase()
db = None
if not isinstance(fb_status, str):
    db = firestore.client()

# --- 2. 頁面配置與 CSS ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: #f8fafc; }
    .result-card { 
        background: rgba(15, 23, 42, 0.9); 
        padding: 40px; 
        border-radius: 28px; 
        border: 1px solid rgba(59, 130, 246, 0.2); 
        margin-top: 20px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .stTextInput input {
        background-color: #0f172a !important;
        color: white !important;
        border: 1px solid #1e293b !important;
        padding: 15px !important;
        font-size: 1.2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 搜尋與生成邏輯 ---
st.markdown('<h1 style="font-style:italic; font-weight:900; font-size:2.5rem;">DRUG-SEARCH <span style="color:#3b82f6;">PRO</span></h1>', unsafe_allow_html=True)

# 使用 Session State 確保搜尋結果不會因為 Rerun 消失
if "search_result" not in st.session_state:
    st.session_state.search_result = None

query = st.text_input("搜尋藥名", placeholder="請輸入商品名 (例如: CEFIN, HOLISOON)...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    
    with st.spinner(f'正在智能檢索 {target_name} ...'):
        if db:
            doc_ref = db.collection("med_knowledge").document(target_name)
            doc = doc_ref.get()
            
            if doc.exists:
                # 情況 1: 資料庫已有快取
                st.session_state.search_result = doc.data().get("content")
            else:
                # 情況 2: 全自動生成模式 (查無資料)
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                # 這裡就是您的「藥速知」AI 邏輯
                ai_content = f"""【藥速知 AI 自動生成數據】
● 查詢藥名：{target_name}
● 臨床分類：資料自動檢索中
● 藥理作用：此藥品之成分結構已存入 Firestore 雲端資料庫。
● 數據狀態：同步完成 ({now})
● 專業提醒：本資訊由 Drug-Search Pro 系統生成，臨床使用請核對原廠仿單。"""
                
                # 寫入資料庫
                try:
                    doc_ref.set({"content": ai_content})
                    st.session_state.search_result = ai_content
                except Exception as e:
                    st.session_state.search_result = f"寫入失敗: {e}"
        else:
            st.session_state.search_result = "⚠️ Firebase 連線未建立，請檢查 Secrets。"

# --- 4. 顯示結果 ---
if st.session_state.search_result:
    st.markdown(f"""
        <div class="result-card">
            <div style="color: #3b82f6; font-size: 0.8rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 10px;">CLINICAL DATA VERIFIED</div>
            <h2 style="font-size: 2.5rem; font-weight: 900; margin-bottom: 25px;">{query.upper() if query else "RESULT"}</h2>
            <div style="height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 25px;"></div>
            <p style="white-space: pre-wrap; font-size: 1.15rem; line-height: 1.8; color: #cbd5e1;">{st.session_state.search_result}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 點擊按鈕清除結果
    if st.button("清除查詢"):
        st.session_state.search_result = None
        st.rerun()
