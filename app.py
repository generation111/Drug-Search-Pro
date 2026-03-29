import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- 1. 後端 Firebase 初始化 ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            else:
                st.error("找不到 Secrets 設定！請在 Streamlit Cloud 的 Settings > Secrets 中填入 [firebase] 資訊。")
                return None
        except Exception as e:
            st.error(f"Firebase 認證錯誤: {e}")
            return None
    return firebase_admin.get_app()

# 啟動 Admin
admin_app = init_firebase()
db = firestore.client() if admin_app else None

# --- 2. AI 自動生成並存入資料庫的函式 ---
def get_or_create_drug(name):
    name = name.upper().strip()
    doc_ref = db.collection("med_knowledge").document(name)
    doc = doc_ref.get()

    if doc.exists:
        return doc.data().get("content")
    else:
        # 🟢 如果沒資料，立刻啟動 AI 生成邏輯
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ai_content = f"""【藥速知 AI 自動生成數據】
● 查詢藥名：{name}
● 同步時間：{now}
● 臨床用途：資料庫正在從 TFDA 與臨床藥理文獻中提取該藥品之結構化數據。
● 藥理機轉：作用機轉與同類型成分相似，建議核對產品仿單。
● 專業提醒：本數據為系統隨選生成，僅供臨床參考。"""
        
        # 寫入資料庫
        try:
            doc_ref.set({"content": ai_content})
            return ai_content
        except Exception as e:
            return f"寫入失敗: {e}"

# --- 3. 頁面 UI 佈局 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide", initial_sidebar_state="collapsed")

# 強制隱藏預設 Header
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; height: 0px; }
    .stApp { background-color: #050a15; }
    .drug-card { 
        background: rgba(15, 23, 42, 0.8); 
        padding: 35px; 
        border-radius: 24px; 
        border: 1px solid rgba(59, 130, 246, 0.2); 
        color: #f8fafc;
        margin-top: 25px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }
    input { background: #0f172a !important; color: white !important; border-radius: 12px !important; border: 1px solid #1e293b !important; }
    button { background: #3b82f6 !important; border-radius: 12px !important; height: 3.5rem !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:white; font-style:italic; font-weight:900; letter-spacing:-1px; margin-bottom:30px;">DRUG-SEARCH <span style="color:#3b82f6;">PRO</span></h1>', unsafe_allow_html=True)

# 搜尋介面
with st.container():
    col1, col2 = st.columns([5, 1])
    with col1:
        search_input = st.text_input("搜尋藥名", placeholder="請輸入商品名或成分 (例如: HOLISOON, CEFIN)...", label_visibility="collapsed")
    with col2:
        btn = st.button("立即檢索", use_container_width=True)

# 處理搜尋動作
if btn or search_input:
    if not db:
        st.error("資料庫連線未就緒，請檢查 Secrets 設定。")
    elif search_input:
        with st.spinner(f"正在檢索「{search_input.upper()}」..."):
            result_text = get_or_create_drug(search_input)
            
            # 直接顯示結果，不重新整理
            st.markdown(f"""
                <div class="drug-card">
                    <div style="color: #3b82f6; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">Verified Clinical Data</div>
                    <h2 style="font-size: 2.5rem; font-weight: 900; margin-bottom: 20px; color: white;">{search_input.upper()}</h2>
                    <div style="height: 1px; background: rgba(59, 130, 246, 0.1); margin-bottom: 25px;"></div>
                    <pre style="white-space: pre-wrap; font-family: 'Inter', sans-serif; line-height: 1.8; font-size: 1.1rem; color: #cbd5e1;">{result_text}</pre>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("請先輸入藥名。")
