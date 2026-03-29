import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 初始化服務 ---
@st.cache_resource
def init_all():
    db_client, ai_client = None, None
    try:
        if not firebase_admin._apps:
            conf = dict(st.secrets["firebase"])
            conf["private_key"] = conf["private_key"].replace("\\n", "\n").strip()
            cred = credentials.Certificate(conf)
            firebase_admin.initialize_app(cred)
        db_client = firestore.client()
    except: pass
    
    if "openai" in st.secrets:
        ai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    return db_client, ai_client

db, ai_client = init_all()

# --- 2. 頁面美化 (慈榛驊業務管理系統風格) ---
st.set_page_config(page_title="慈榛驊藥品查詢系統", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: white; }
    .drug-box { 
        background: #0f172a; padding: 25px; border-radius: 15px; 
        border-left: 5px solid #3b82f6; margin-top: 20px;
    }
    .label { color: #3b82f6; font-weight: bold; margin-right: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h2 style="font-weight:900;">慈榛驊 <span style="color:#3b82f6;">藥品資料查詢系統</span></h2>', unsafe_allow_html=True)

# --- 3. 搜尋邏輯 ---
query = st.text_input("輸入藥品商品名或成分名", placeholder="例如: HOLISOON, CEFIN, CHEF...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    
    with st.spinner(f'正在檢索 {target} 臨床藥理資料...'):
        full_info = ""
        is_cached = False

        # 1. 優先從資料庫調閱已存資料
        if db:
            try:
                doc = db.collection("med_knowledge").document(target).get(timeout=3)
                if doc.exists:
                    full_info = doc.data().get("content")
                    is_cached = True
            except: pass

        # 2. 資料庫無紀錄，調用 AI 檢索精確藥理資訊
        if not is_cached and ai_client:
            try:
                # 強制 AI 遵守 TFDA/NHI 結構
                response = ai_client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {"role": "system", "content": """你是一位專業的臨床藥師。請針對使用者提供的藥名，檢索並整理出精確的臨床資料。
                        必須包含以下結構：
                        1. 中英文商品名及主要成分(學名)。
                        2. 臨床適應症 (Indication)。
                        3. 用法用量 (Dosage)。
                        4. 藥理機轉 (Mechanism of Action)。
                        5. 重要禁忌與副作用 (Contraindications/Side Effects)。
                        請確保內容嚴謹，並使用繁體中文。若該藥名為特定廠牌(如慈榛驊代理商品)，請優先以該商品資訊為主。"""},
                        {"role": "user", "content": f"請提供藥品 {target} 的完整臨床資料。"}
                    ],
                    temperature=0.2 # 降低隨機性，確保資料精確
                )
                full_info = response.choices[0].message.content
                
                # 自動存檔供下次查詢
                if db:
                    db.collection("med_knowledge").document(target).set({
                        "content": full_info, 
                        "update_time": datetime.datetime.now()
                    })
            except Exception as e:
                full_info = f"查詢出錯，請檢查網路連線或 API 金鑰設定。({e})"

        # 3. 顯示結構化結果
        st.markdown(f"""
            <div class="drug-box">
                <h3 style="color:white; margin-bottom:15px;">🔍 檢索結果：{target}</h3>
                <div style="line-height:1.8; color:#cbd5e1; white-space: pre-wrap;">{full_info}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請輸入藥名啟動專業臨床資料檢索。")
