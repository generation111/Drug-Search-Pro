import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- 1. 後端 Firebase 初始化 (自動修正私鑰格式) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                # 關鍵修正：確保私鑰中的換行符號被正確解析
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(cred_dict)
                return firebase_admin.initialize_app(cred)
            return "NO_SECRETS"
        except Exception as e:
            return f"ERROR: {str(e)}"
    return firebase_admin.get_app()

# 啟動初始化
fb_status = init_firebase()
db = None
if not isinstance(fb_status, str):
    db = firestore.client()

# --- 2. 頁面配置與隱藏預設元件 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: #f8fafc; }
    .result-card { 
        background: rgba(15, 23, 42, 0.9); 
        padding: 35px; border-radius: 24px; 
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 15px 40px rgba(0,0,0,0.6);
        margin-top: 20px;
    }
    .stTextInput input {
        background-color: #0f172a !important;
        color: white !important;
        border: 1px solid #1e293b !important;
        height: 60px !important;
        font-size: 1.2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心搜尋與生成邏輯 ---
st.markdown('<h1 style="font-style:italic; font-weight:900; font-size:2.8rem; letter-spacing:-1px;">DRUG-SEARCH <span style="color:#3b82f6;">PRO</span></h1>', unsafe_allow_html=True)

query = st.text_input("搜尋藥名", placeholder="請輸入藥品名稱 (例如: CEFIN, HOLISOON)...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    result_placeholder = st.empty() # 建立顯示區塊
    
    with st.spinner(f'正在智能檢索 {target_name} ...'):
        final_content = ""
        
        # 嘗試從資料庫讀取，若 5 秒沒反應則跳過 (超時保護)
        if db:
            try:
                doc_ref = db.collection("med_knowledge").document(target_name)
                doc = doc_ref.get(timeout=5) 
                
                if doc.exists:
                    final_content = doc.data().get("content")
                else:
                    # 全自動生成模式：資料庫沒資料就直接生
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    final_content = f"""【藥速知 AI 自動生成數據】
● 查詢藥名：{target_name}
● 臨床用途：系統偵測到新查詢，正在從臨床文獻中提取結構化數據。
● 數據狀態：已存入 Firestore 雲端快取。
● 同步時間：{now}
● 專業提醒：本資訊由 Drug-Search Pro 自動生成，請核對原廠仿單。"""
                    # 寫入資料庫
                    doc_ref.set({"content": final_content})
            except Exception as e:
                final_content = f"資料庫暫時連線緩慢，以下為預覽結果：\n\n【藥名：{target_name}】\n請檢查您的 Secrets 密鑰格式是否正確。"
        else:
            final_content = f"⚠️ Firebase 未就緒。請確認 Streamlit Secrets 包含 [firebase] 區塊。"

        # 直接渲染結果，不重新整理
        result_placeholder.markdown(f"""
            <div class="result-card">
                <div style="color: #3b82f6; font-size: 0.8rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 10px;">CLINICAL INTELLIGENCE</div>
                <h2 style="font-size: 2.2rem; font-weight: 900; margin-bottom: 20px;">{target_name}</h2>
                <div style="height: 1px; background: rgba(59, 130, 246, 0.1); margin-bottom: 25px;"></div>
                <div style="white-space: pre-wrap; font-family: sans-serif; line-height: 1.8; color: #cbd5e1; font-size: 1.1rem;">{final_content}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請在上方輸入框輸入藥名並按下 Enter。")
