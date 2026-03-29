import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit.components.v1 as components
import datetime

# --- 1. 後端 Firebase 初始化 ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Admin 初始化失敗: {e}")
            return None
    return firebase_admin.get_app()

admin_app = init_firebase()
db_admin = firestore.client() if admin_app else None

# --- 2. AI 自動生成邏輯 ---
def ai_generate_and_save(drug_name):
    if not db_admin: return False
    drug_name = drug_name.upper()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    ai_content = f"""【藥速知 AI 自動生成數據】
● 商品名稱：{drug_name}
● 數據狀態：同步完成 ({now})
● 臨床用途：此藥品資料已透過 AI 進行結構化整理。
● 藥理作用：請參考 TFDA 最新公告仿單。
● 專業提醒：本資訊僅供參考，臨床決策請諮詢藥師。"""
    
    try:
        db_admin.collection("med_knowledge").document(drug_name).set({"content": ai_content})
        return True
    except:
        return False

# --- 3. 介面與搜尋邏輯 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide")

# 使用 Streamlit 原生輸入框來避免 iframe 權限問題
st.markdown('<h1 style="color:white; font-style:italic; font-weight:900;">DRUG-SEARCH <span style="color:#3b82f6;">PRO</span></h1>', unsafe_allow_html=True)

# 建立搜尋列
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("", placeholder="輸入藥名 (例如: CHEF)...", label_visibility="collapsed")
with col2:
    search_btn = st.button("立即檢索", use_container_width=True)

if query or search_btn:
    name = query.strip().upper()
    if name:
        # 先檢查資料庫
        doc = db_admin.collection("med_knowledge").document(name).get()
        
        if doc.exists:
            result = doc.data().get("content")
        else:
            # 沒資料時，直接在 Python 端執行生成，不需跳轉
            with st.status(f"正在為您同步「{name}」的數據...", expanded=True) as status:
                success = ai_generate_and_save(name)
                if success:
                    status.update(label="數據同步成功！", state="complete")
                    # 重新讀取剛生成的資料
                    result = ai_generate_and_save(name) # 這裡直接拿內容
                    st.rerun()
                else:
                    result = "生成失敗，請檢查資料庫權限。"

        # 顯示結果
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.8); padding: 40px; border-radius: 24px; border: 1px solid rgba(59, 130, 246, 0.2); color: #e2e8f0; margin-top: 20px;">
            <h2 style="color: #3b82f6; font-weight: 900; font-size: 2rem; margin-bottom: 20px;">{name}</h2>
            <pre style="white-space: pre-wrap; font-family: sans-serif; line-height: 1.8; font-size: 1.1rem;">{doc.data().get('content') if doc.exists else '資料已存入，請再次點擊搜尋。'}</pre>
        </div>
        """, unsafe_allow_html=True)

# --- 背景樣式 ---
st.markdown("""
<style>
    .stApp { background: #050a15; }
    input { background-color: rgba(15, 23, 42, 0.8) !important; color: white !important; border: 1px solid rgba(59, 130, 246, 0.3) !important; border-radius: 12px !important; padding: 25px !important; font-size: 1.2rem !important; }
    button { background-color: #3b82f6 !important; border-radius: 12px !important; padding: 12px !important; font-weight: bold !important; height: 65px !important; }
</style>
""", unsafe_allow_html=True)
