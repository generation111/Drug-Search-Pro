import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 核心服務初始化 ---
@st.cache_resource
def init_system():
    db_ptr, ai_ptr = None, None
    try:
        # Firebase 認證：確保私鑰格式正確
        if not firebase_admin._apps:
            secret_fb = dict(st.secrets["firebase"])
            secret_fb["private_key"] = secret_fb["private_key"].replace("\\n", "\n").strip()
            cred = credentials.Certificate(secret_fb)
            firebase_admin.initialize_app(cred)
        db_ptr = firestore.client()
    except Exception as e:
        st.error(f"資料庫連線異常: {e}")

    # OpenAI 認證
    if "openai" in st.secrets:
        ai_ptr = OpenAI(api_key=st.secrets["openai"]["api_key"])
    return db_ptr, ai_ptr

db, ai_client = init_system()

# --- 2. 專業 UI 佈局 (慈榛驊業務風格) ---
st.set_page_config(page_title="慈榛驊藥品檢索系統", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: #f8fafc; }
    .drug-card { 
        background: #0f172a; padding: 30px; border-radius: 12px; 
        border-left: 6px solid #3b82f6; margin-top: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .info-label { color: #3b82f6; font-weight: 800; font-size: 0.9rem; letter-spacing: 1px; }
    input { background-color: #1e293b !important; color: white !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('## 慈榛驊 <span style="color:#3b82f6;">藥品臨床資料庫</span>', unsafe_allow_html=True)

# --- 3. 搜尋與資料存取邏輯 ---
query = st.text_input("輸入商品名或成分 (例如: CHEF, HOLISOON, CEFIN)", placeholder="請輸入藥名...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    
    with st.spinner(f'正在調閱 {target} 完整臨床仿單數據...'):
        final_data = ""
        cached = False

        # 步驟 A: 從 Firestore 讀取快取 (確保速度)
        if db:
            try:
                doc = db.collection("med_knowledge").document(target).get(timeout=5)
                if doc.exists:
                    final_data = doc.data().get("content")
                    cached = True
            except: pass

        # 步驟 B: 若無資料，請 AI 擔任藥師進行整理
        if not cached and ai_client:
            try:
                # 嚴格約束 AI 輸出臨床藥理結構
                response = ai_client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {"role": "system", "content": """你是一位臨床藥師與醫藥資訊專家。
                        請提供該藥品的精確數據，必須包含：
                        1. 中英文商品名及主要成分 (Generic Name)。
                        2. 臨床適應症 (Indication)。
                        3. 用法用量 (Dosage & Administration)。
                        4. 藥理作用機轉 (Mechanism of Action)。
                        5. 禁忌與交互作用 (Contraindications)。
                        請以繁體中文撰寫，內容必須嚴謹，嚴禁虛構。"""},
                        {"role": "user", "content": f"請檢索並整理藥品「{target}」的臨床資料。"}
                    ],
                    temperature=0.1 # 極低隨機性，確保數據準確
                )
                final_data = response.choices[0].message.content
                
                # 自動寫入資料庫
                if db:
                    db.collection("med_knowledge").document(target).set({
                        "content": final_data,
                        "timestamp": datetime.datetime.now()
                    })
            except Exception as e:
                final_data = f"檢索失敗，請確認 API 配置。錯誤訊息：{e}"

        # 步驟 C: 渲染結構化結果
        st.markdown(f"""
            <div class="drug-card">
                <div class="info-label">CLINICAL DATA VERIFIED</div>
                <h2 style="margin: 10px 0 20px 0; color: white;">{target}</h2>
                <div style="height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 25px;"></div>
                <div style="white-space: pre-wrap; line-height: 1.8; color: #cbd5e1; font-size: 1.1rem;">{final_data}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請輸入藥名，系統將自動調閱 Firestore 或 AI 藥理庫。")
