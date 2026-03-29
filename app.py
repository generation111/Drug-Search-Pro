import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 服務初始化 ---
@st.cache_resource
def init_services():
    db_client, ai_client = None, None
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
    
    if "openai" in st.secrets:
        ai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    return db_client, ai_client

db, ai_client = init_services()

# --- 2. 介面樣式 ---
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

# --- 3. 搜尋核心 ---
query = st.text_input("搜尋藥名", placeholder="輸入藥名後按下 Enter...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    
    # 建立顯示區塊
    card_container = st.container()
    
    with card_container:
        st.markdown(f"""
            <div class="result-card">
                <div style="color:#3b82f6; font-weight:800; font-size:0.8rem; letter-spacing:2px; margin-bottom:10px;">CLINICAL INTELLIGENCE</div>
                <h2 style="font-size:2.2rem; font-weight:900;">{target_name}</h2>
                <hr style="opacity:0.1; margin:20px 0;">
            </div>
        """, unsafe_allow_html=True)
        
        # 準備顯示內容的佔位符
        response_placeholder = st.empty()
        full_response = ""

        # 1. 嘗試從 Firestore 讀取 (快取優先)
        found_in_db = False
        if db:
            try:
                doc = db.collection("med_knowledge").document(target_name).get(timeout=3)
                if doc.exists:
                    full_response = doc.data().get("content")
                    response_placeholder.markdown(f'<div style="white-space:pre-wrap; line-height:1.8; color:#cbd5e1; font-size:1.1rem; padding: 0 30px 30px 30px;">{full_response}</div>', unsafe_allow_html=True)
                    found_in_db = True
            except: pass

        # 2. 若沒資料，啟動 OpenAI 流式生成
        if not found_in_db and ai_client:
            try:
                stream = ai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "你是一位資深藥品行銷與醫藥企業高管。請提供藥品的學名、臨床用途、藥理作用及注意事項。語氣專業、結構化，使用繁體中文。"},
                        {"role": "user", "content": f"分析藥品：{target_name}"}
                    ],
                    stream=True, # 開啟流式傳輸
                    temperature=0.3
                )
                
                # 字幕式彈出效果
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(f'<div style="white-space:pre-wrap; line-height:1.8; color:#cbd5e1; font-size:1.1rem; padding: 0 30px 30px 30px;">{full_response}</div>', unsafe_allow_html=True)
                
                # 3. 生成完畢後，存入資料庫
                if db:
                    db.collection("med_knowledge").document(target_name).set({
                        "content": full_response,
                        "updated_at": datetime.datetime.now()
                    })
            except Exception as e:
                st.error(f"AI 服務暫時無法回應: {e}")
else:
    st.info("💡 請輸入藥名啟動全自動 AI 檢索系統。")
