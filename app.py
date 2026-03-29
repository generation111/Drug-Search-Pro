import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 初始化 Firebase & OpenAI ---
@st.cache_resource
def init_services():
    # Firebase 初始化
    if not firebase_admin._apps:
        try:
            cred_dict = dict(st.secrets["firebase"])
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except:
            pass
    
    # OpenAI 初始化
    client = None
    if "openai" in st.secrets:
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    return firestore.client(), client

db, ai_client = init_services()

# --- 2. AI 生成邏輯 (醫藥商務口吻) ---
def generate_medical_data(drug_name):
    if not ai_client:
        return "⚠️ OpenAI API Key 未設定，無法生成資料。"
    
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4-turbo", # 或使用 gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "你是一位資深藥品行銷與醫藥企業高管。請針對使用者提供的藥品名稱，檢索其學名、臨床用途、藥理作用及注意事項。請使用繁體中文，語氣需專業且具備商務推廣調性，並嚴格遵守結構化格式。"},
                {"role": "user", "content": f"請分析藥品：{drug_name}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失敗: {str(e)}"

# --- 3. 頁面 UI 配置 ---
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

st.markdown('<h1 style="font-style:italic; font-weight:900; font-size:2.8rem; letter-spacing:-1px;">DRUG-SEARCH <span style="color:#3b82f6;">PRO</span></h1>', unsafe_allow_html=True)

# --- 4. 搜尋與自動化存檔 ---
query = st.text_input("搜尋藥名", placeholder="請輸入藥品名稱 (如: CEFIN, HOLISOON)...", label_visibility="collapsed")

if query:
    target_name = query.strip().upper()
    result_placeholder = st.empty()
    
    with st.spinner(f'正在調用 AI 臨床數據庫檢索 {target_name} ...'):
        final_content = ""
        
        if db:
            doc_ref = db.collection("med_knowledge").document(target_name)
            doc = doc_ref.get()
            
            if doc.exists:
                # 情況 A: 資料庫已有快取，直接讀取
                final_content = doc.data().get("content")
            else:
                # 情況 B: 全自動 OpenAI 生成
                final_content = generate_medical_data(target_name)
                # 自動寫入 Firestore 供下次快取
                try:
                    doc_ref.set({
                        "content": final_content,
                        "updated_at": datetime.datetime.now()
                    })
                except:
                    pass
        
        # 渲染卡片
        result_placeholder.markdown(f"""
            <div class="result-card">
                <div style="color: #3b82f6; font-size: 0.8rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 10px;">AI POWERED CLINICAL ANALYSIS</div>
                <h2 style="font-size: 2.5rem; font-weight: 900; margin-bottom: 25px;">{target_name}</h2>
                <div style="height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 25px;"></div>
                <div style="white-space: pre-wrap; font-family: sans-serif; line-height: 1.8; color: #cbd5e1; font-size: 1.15rem;">{final_content}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請輸入藥名啟動全自動 AI 檢索系統。")
