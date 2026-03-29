import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 初始化服務 (加入超時與異常保護) ---
@st.cache_resource
def init_services():
    db_client = None
    ai_client = None
    
    # Firebase 初始化
    try:
        if not firebase_admin._apps:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                # 徹底處理私鑰格式，防止 RetryError
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n").strip()
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("Missing Firebase Secrets")
        db_client = firestore.client()
    except Exception as e:
        st.warning(f"資料庫連線暫時受阻，切換至純 AI 模式。")

    # OpenAI 初始化
    try:
        if "openai" in st.secrets:
            ai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    except Exception as e:
        st.error(f"OpenAI 初始化失敗: {e}")
        
    return db_client, ai_client

db, ai_client = init_services()

# --- 2. AI 生成邏輯 ---
def generate_medical_data(drug_name):
    if not ai_client:
        return "⚠️ OpenAI API 未就緒。"
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o", # 建議使用更穩定的 gpt-4o 或 gpt-4-turbo
            messages=[
                {"role": "system", "content": "你是一位資深藥品行銷與醫藥企業高管。請提供藥品的學名、臨床用途、藥理作用及注意事項。語氣需專業、結構化，並使用繁體中文。"},
                {"role": "user", "content": f"分析藥品：{drug_name}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成異常: {str(e)}"

# --- 3. UI 介面 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #050a15; color: #f8fafc; }
    .result-card { 
        background: rgba(15, 23, 42, 0.9); padding: 35px; border-radius: 24px; 
        border: 1px solid rgba(59, 130, 246, 0.3); margin-top: 20px;
    }
    input { background-color: #0f172a !important; color: white !important; height: 60px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('# DRUG-SEARCH <span style="color:#3b82f6;">PRO</span>', unsafe_allow_html=True)

# --- 4. 搜尋核心 (加入 RetryError 攔截) ---
query = st.text_input("搜尋藥名", placeholder="請輸入藥品名稱...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    result_placeholder = st.empty()
    
    with st.spinner(f'智能檢索 {target_name} 中...'):
        content = ""
        # 優先嘗試從資料庫讀取，失敗則直接轉 AI
        if db:
            try:
                # 這裡設定 timeout 避免 RetryError 導致頁面卡死
                doc_ref = db.collection("med_knowledge").document(target_name)
                doc = doc_ref.get(timeout=10) 
                if doc.exists:
                    content = doc.data().get("content")
                else:
                    content = generate_medical_data(target_name)
                    doc_ref.set({"content": content, "time": datetime.datetime.now()})
            except Exception:
                # 若發生 RetryError 或任何連線問題，直接由 AI 輸出，不顯示報錯
                content = generate_medical_data(target_name)
        else:
            content = generate_medical_data(target_name)

        # 渲染結果
        result_placeholder.markdown(f"""
            <div class="result-card">
                <div style="color:#3b82f6; font-weight:800; font-size:0.8rem; letter-spacing:2px; margin-bottom:10px;">CLINICAL ANALYSIS</div>
                <h2 style="font-size:2.2rem; font-weight:900;">{target_name}</h2>
                <hr style="opacity:0.1; margin:20px 0;">
                <div style="white-space:pre-wrap; line-height:1.8; color:#cbd5e1;">{content}</div>
            </div>
        """, unsafe_allow_html=True)
