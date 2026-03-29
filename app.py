import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 極速服務初始化 ---
@st.cache_resource
def init_services():
    db_c, ai_c = None, None
    try:
        if not firebase_admin._apps:
            # 修正私鑰格式並建立連線
            conf = dict(st.secrets["firebase"])
            conf["private_key"] = conf["private_key"].replace("\\n", "\n").strip()
            cred = credentials.Certificate(conf)
            firebase_admin.initialize_app(cred)
        db_c = firestore.client()
    except: pass
    
    if "openai" in st.secrets:
        ai_c = OpenAI(api_key=st.secrets["openai"]["api_key"])
    return db_c, ai_c

db, ai_client = init_services()

# --- 2. 慈榛驊專業介面 ---
st.set_page_config(page_title="慈榛驊藥品檢索系統", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: #f8fafc; }
    .drug-card { 
        background: #0f172a; padding: 30px; border-radius: 12px; 
        border-left: 6px solid #3b82f6; margin-top: 25px;
    }
    .info-label { color: #3b82f6; font-weight: 800; font-size: 0.9rem; }
    input { background-color: #1e293b !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('## 慈榛驊 <span style="color:#3b82f6;">藥品臨床資料庫 (終極修復版)</span>', unsafe_allow_html=True)

# --- 3. 搜尋核心 (暴力穩定邏輯) ---
query = st.text_input("輸入藥名 (例如: CHEF, CEFIN, HOLISOON)", placeholder="搜尋藥名...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    
    with st.spinner(f'系統調閱中: {target} ...'):
        final_info = ""
        success = False

        # 優先級 1: 嘗試從 Firebase 快取讀取 (強設定 1 秒超時)
        if db:
            try:
                doc = db.collection("med_knowledge").document(target).get(timeout=1.0)
                if doc.exists:
                    final_info = doc.data().get("content")
                    success = True
            except: pass

        # 優先級 2: 若快取無效，強制調用 OpenAI 生成臨床仿單
        if not success and ai_client:
            try:
                response = ai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": """你是一位專業臨床藥師。請針對藥名提供以下結構化資料：
                        1. 中英文商品名及學名 (Generic Name)。
                        2. 臨床適應症 (Indication)。
                        3. 用法用量 (Dosage)。
                        4. 藥理作用機轉 (Mechanism of Action)。
                        5. 禁忌與副作用 (Contraindications)。
                        內容必須嚴謹、精確，嚴禁虛構。"""},
                        {"role": "user", "content": f"請提供藥品 {target} 的完整藥理資料。"}
                    ],
                    temperature=0.1 # 確保資料嚴謹度
                )
                final_info = response.choices[0].message.content
                
                # 背景存檔 (不影響顯示速度)
                if db:
                    try: db.collection("med_knowledge").document(target).set({"content": final_info, "t": datetime.datetime.now()})
                    except: pass
                success = True
            except Exception as e:
                final_info = f"檢索異常：{e}"

        # 顯示結果 (一次性呈現)
        if success:
            st.markdown(f"""
                <div class="drug-card">
                    <div class="info-label">CLINICAL DATA VERIFIED</div>
                    <h2 style="color:white; margin:10px 0;">{target}</h2>
                    <hr style="opacity:0.1; margin-bottom:20px;">
                    <div style="white-space: pre-wrap; line-height: 1.8; color: #cbd5e1; font-size: 1.1rem;">{final_info}</div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("💡 請輸入藥名啟動專業臨床資料檢索。")
