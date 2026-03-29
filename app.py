import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from openai import OpenAI

# --- 1. 核心服務初始化 (確保完全獨立) ---
def init_app():
    # Firebase 初始化：解決密鑰格式與連線鎖死
    if not firebase_admin._apps:
        try:
            fb_conf = dict(st.secrets["firebase"])
            fb_conf["private_key"] = fb_conf["private_key"].replace("\\n", "\n").strip()
            cred = credentials.Certificate(fb_conf)
            firebase_admin.initialize_app(cred)
        except:
            pass
    
    # OpenAI 初始化
    ai_client = None
    if "openai" in st.secrets:
        ai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    return firestore.client(), ai_client

db, client = init_app()

# --- 2. 頁面精確配置 (移除無關風格) ---
st.set_page_config(page_title="藥速知 MedQuick", layout="wide")
st.markdown("""
    <style>
    [data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: #0e1117; color: white; }
    .drug-result { 
        background: #1e293b; padding: 2rem; border-radius: 10px; 
        border: 1px solid #334155; margin-top: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💊 藥速知 MedQuick")
st.caption("專業藥品臨床仿單與藥理資料檢索系統")

# --- 3. 搜尋邏輯 (移除轉圈圈卡死) ---
query = st.text_input("輸入藥名 (商品名或成分名)", placeholder="例如: CHEF, CEFIN, HOLISOON...", label_visibility="collapsed")

if query:
    target = query.strip().upper()
    
    # 使用 container 確保結果能即時刷出
    res_container = st.empty()
    
    with st.spinner(f'正在檢索 {target} 臨床數據...'):
        final_info = ""
        is_ready = False

        # 1. 優先從資料庫撈取 (限時 1 秒，失敗直接跳 AI)
        if db:
            try:
                doc = db.collection("med_knowledge").document(target).get(timeout=1.0)
                if doc.exists:
                    final_info = doc.data().get("content")
                    is_ready = True
            except:
                pass

        # 2. 若無快取，調用 OpenAI 進行專業藥理整理
        if not is_ready and client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "你是一位臨床藥師。請針對藥名提供：1.學名(Generic Name) 2.臨床適應症 3.用法用量 4.藥理機轉 5.重要禁忌。請使用繁體中文，內容嚴謹。"},
                        {"role": "user", "content": f"請檢索藥品 {target} 的臨床資料。"}
                    ],
                    temperature=0.2
                )
                final_info = response.choices[0].message.content
                
                # 異步存檔
                if db:
                    db.collection("med_knowledge").document(target).set({
                        "content": final_info,
                        "updated": datetime.datetime.now()
                    })
                is_ready = True
            except Exception as e:
                final_info = f"檢索服務暫時無法回應，請檢查 API 設定。({e})"

        # 3. 顯示結果 (一次性呈現)
        res_container.markdown(f"""
            <div class="drug-result">
                <h2 style="color:#38bdf8; margin-bottom:1rem;">{target} 臨床分析報告</h2>
                <div style="white-space: pre-wrap; line-height: 1.7; font-size: 1.1rem; color: #e2e8f0;">{final_info}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("💡 請在上方輸入框輸入藥名並按下 Enter 鍵。")
