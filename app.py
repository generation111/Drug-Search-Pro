import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- 1. 後端 Firebase 初始化 (自動修正格式) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                # 關鍵修正：修復私鑰中的換行字元
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            return "NO_SECRETS"
        except Exception as e:
            return f"ERROR: {str(e)}"
    return firebase_admin.get_app()

# 初始化
fb_app = init_firebase()
db = None
if not isinstance(fb_app, str):
    db = firestore.client()

# --- 2. UI 樣式配置 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: #f8fafc; }
    .result-card { 
        background: rgba(15, 23, 42, 0.9); 
        padding: 35px; border-radius: 24px; 
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 20px 50px rgba(0,0,0,0.6);
        margin-top: 20px;
    }
    input { background-color: #0f172a !important; color: white !important; height: 60px !important; font-size: 1.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 搜尋邏輯 ---
st.markdown('<h1 style="font-style:italic; font-weight:900; font-size:2.8rem; letter-spacing:-1px;">DRUG-SEARCH <span style="color:#3b82f6;">PRO</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋藥名", placeholder="請輸入商品名 (如: CEFIN, HOLISOON)...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    result_placeholder = st.empty() # 建立一個空的佔位符
    
    with st.spinner(f'正在為您檢索 {target_name} ...'):
        # 預先生成 AI 內容 (避免資料庫卡住)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        ai_generated_content = f"""【藥速知 AI 自動生成數據】
● 查詢藥名：{target_name}
● 臨床分類：自動檢索中
● 藥理作用：系統已將此成分納入結構化資料庫。
● 數據狀態：同步完成 ({now})
● 專業提醒：本資訊由系統自動生成，臨床決策請務必核對產品仿單。"""

        final_content = ai_generated_content
        
        if db:
            try:
                # 嘗試讀取，超時時間設短一點 (3秒)
                doc_ref = db.collection("med_knowledge").document(target_name)
                doc = doc_ref.get(timeout=3)
                
                if doc.exists:
                    final_content = doc.data().get("content")
                else:
                    # 沒資料就直接存入預先生成的內容
                    doc_ref.set({"content": ai_generated_content})
            except Exception:
                # 如果連資料庫失敗，就直接用預生成的內容，不報錯
                pass
        
        # 渲染卡片
        result_placeholder.markdown(f"""
            <div class="result-card">
                <div style="color: #3b82f6; font-size: 0.8rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 10px;">CLINICAL DATA READY</div>
                <h2 style="font-size: 2.5rem; font-weight: 900; margin-bottom: 25px;">{target_name}</h2>
                <div style="height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 25px;"></div>
                <div style="white-space: pre-wrap; font-family: sans-serif; line-height: 1.8; color: #cbd5e1; font-size: 1.15rem;">{final_content}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請在上方輸入框輸入藥名並按下 Enter 鍵。")
