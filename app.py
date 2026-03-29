import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 服務初始化 ---
@st.cache_resource
def init_services():
    db_client, ai_client = None, None
    # Firebase
    if not firebase_admin._apps:
        try:
            cred_dict = dict(st.secrets["firebase"])
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n").strip()
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db_client = firestore.client()
        except: pass
    else:
        db_client = firestore.client()
    
    # OpenAI
    if "openai" in st.secrets:
        ai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    return db_client, ai_client

db, ai_client = init_services()

# --- 2. AI 核心：醫藥企業高管口吻 ---
def generate_ai_analysis(drug_name):
    if not ai_client: return "OpenAI API 未設定。"
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位資深藥品行銷與醫藥企業高管。請提供藥品的學名、臨床用途、藥理作用及注意事項。語氣專業、結構化，使用繁體中文。"},
                {"role": "user", "content": f"分析藥品：{drug_name}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 暫時無法生成: {str(e)}"

# --- 3. 頁面佈局 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: white; }
    .result-card { 
        background: rgba(15, 23, 42, 0.9); padding: 30px; border-radius: 20px; 
        border: 1px solid rgba(59, 130, 246, 0.3); margin-top: 20px;
    }
    input { background-color: #0f172a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('# DRUG-SEARCH <span style="color:#3b82f6;">PRO</span>', unsafe_allow_html=True)

# --- 4. 搜尋與回顯邏輯 (解決卡死關鍵) ---
query = st.text_input("搜尋藥名", placeholder="輸入藥名並按下 Enter...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    
    with st.spinner(f'🚀 正在為您調閱 {target_name} 臨床數據...'):
        content = ""
        # 1. 嘗試從 Firestore 讀取
        found_in_db = False
        if db:
            try:
                doc_ref = db.collection("med_knowledge").document(target_name)
                doc = doc_ref.get(timeout=5)
                if doc.exists:
                    content = doc.data().get("content")
                    found_in_db = True
            except: pass

        # 2. 若沒資料，啟動 AI 生成
        if not found_in_db:
            content = generate_ai_analysis(target_name)
            # 3. 顯示完畢後，背景自動存檔 (不讓使用者等待)
            if db and "AI 暫時無法" not in content:
                try:
                    db.collection("med_knowledge").document(target_name).set({
                        "content": content,
                        "updated_at": datetime.datetime.now()
                    })
                except: pass

        # 4. 渲染卡片
        st.markdown(f"""
            <div class="result-card">
                <div style="color:#3b82f6; font-weight:800; font-size:0.8rem; letter-spacing:2px; margin-bottom:10px;">CLINICAL INTELLIGENCE</div>
                <h2 style="font-size:2.2rem; font-weight:900;">{target_name}</h2>
                <hr style="opacity:0.1; margin:20px 0;">
                <div style="white-space:pre-wrap; line-height:1.8; color:#cbd5e1; font-size:1.1rem;">{content}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請輸入藥名啟動全自動 AI 檢索系統。")
