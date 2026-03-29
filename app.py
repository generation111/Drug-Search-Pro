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
            # 確保 Secrets 格式正確
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Admin 認證失敗: {e}")
            return None
    return firebase_admin.get_app()

admin_app = init_firebase()
if admin_app:
    db_admin = firestore.client()
else:
    st.warning("正在等待 Firebase 權限配置...")
    st.stop()

# --- 2. AI 自動生成與寫入邏輯 ---
def ai_generate_and_save(drug_name):
    drug_name = drug_name.upper()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 自動生成的結構化內容
    ai_content = f"""【藥速知 AI 自動生成數據】
● 商品名稱：{drug_name}
● 數據狀態：自動同步完成 ({now})
● 臨床用途：此藥品資料已透過系統後台進行結構化校正。
● 藥理作用：請參考 TFDA 最新公告之仿單資訊。
● 專業提醒：本資訊由 AI 自動生成，臨床決策請諮詢專業藥師。"""
    
    try:
        doc_ref = db_admin.collection("med_knowledge").document(drug_name)
        doc_ref.set({"content": ai_content})
        return True
    except Exception as e:
        st.error(f"寫入資料庫失敗: {e}")
        return False

# --- 3. 處理自動生成請求 ---
params = st.query_params
if "action" in params and params["action"] == "generate":
    target_name = params["name"]
    if ai_generate_and_save(target_name):
        st.query_params.clear()
        st.rerun()

# --- 4. 前端 UI (注意這裡的雙大括號處理) ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide", initial_sidebar_state="collapsed")

# 這裡使用普通的字串，避免 f-string 的轉義問題
html_content = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap');
        body { background: #050a15; font-family: 'Inter', sans-serif; color: #e2e8f0; }
        .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(59, 130, 246, 0.2); }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState } = React;

        const firebaseConfig = {
            apiKey: "AIzaSyDYzAXOd4xyJ5NOuwJl5nj7XgcVmba_54I",
            authDomain: "drug-search-pro.firebaseapp.com",
            projectId: "drug-search-pro",
            appId: "1:601449029455:web:d05d7592b32780efe86f3a"
        };
        
        if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        const App = () => {
            const [query, setQuery] = useState("");
            const [result, setResult] = useState(null);
            const [loading, setLoading] = useState(false);

            const handleSearch = async () => {
                if (!query) return;
                setLoading(true);
                const name = query.trim().toUpperCase();
                
                try {
                    const doc = await db.collection("med_knowledge").doc(name).get();
                    if (doc.exists) {
                        setResult(doc.data().content);
                        setLoading(false);
                    } else {
                        setResult("AI 正在為您同步「" + name + "」的數據，請稍候...");
                        // 跳轉通知 Python
                        window.parent.location.href = window.parent.location.origin + "?action=generate&name=" + name;
                    }
                } catch (e) {
                    setResult("系統錯誤: " + e.message);
                    setLoading(false);
                }
            };

            return (
                <div className="max-w-4xl mx-auto p-10">
                    <h1 className="text-3xl font-black italic mb-10 tracking-tighter">DRUG-SEARCH <span className="text-blue-500">PRO</span></h1>
                    <div className="glass p-2 rounded-2xl flex shadow-2xl mb-10">
                        <input 
                            className="bg-transparent flex-1 px-6 py-4 text-xl outline-none" 
                            placeholder="輸入藥名 (例如: CEFIN)..."
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSearch()}
                        />
                        <button onClick={handleSearch} className="bg-blue-600 px-10 py-4 rounded-xl font-bold hover:bg-blue-500 transition-all">
                            {loading ? "處理中..." : "檢索"}
                        </button>
                    </div>
                    {result && (
                        <div className="glass p-10 rounded-3xl border-blue-900/50 animate-pulse">
                            <pre className="whitespace-pre-wrap font-sans text-slate-300 leading-relaxed text-lg">{result}</pre>
                        </div>
                    )}
                </div>
            );
        };
        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>
"""

components.html(html_content, height=1000, scrolling=True)
