import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit.components.v1 as components
import json

# --- 1. 後端 Firebase 初始化 (管理員權限) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            return firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

try:
    app = init_firebase()
    db_admin = firestore.client()
except Exception as e:
    st.error(f"Firebase Admin 初始化失敗: {e}")

# --- 2. AI 生成與自動寫入邏輯 ---
def ai_generate_and_save(drug_name):
    """
    這是一個模擬 AI 生成的函式。
    俊林，你之後可以在這裡接入 OpenAI 的 API。
    """
    drug_name = drug_name.upper()
    
    # 這裡你可以換成 OpenAI 的調用代碼
    ai_content = f"""【藥速知 AI 自動生成】
● 商品名：{drug_name}
● 成分學名：(系統自動檢索中)
● 臨床用途：用於治療相關感染或緩解症狀。
● 藥理作用：本品為處方用藥，詳細機轉需參考 TFDA 公告。
● 注意事項：請依照專業醫療人員指示使用。
● 數據來源：臨床資料庫自動同步 ({time_str()})"""
    
    # 自動寫入 Firestore
    doc_ref = db_admin.collection("med_knowledge").document(drug_name)
    doc_ref.set({"content": ai_content})
    return ai_content

def time_str():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- 3. Streamlit 介面與橋接器 ---
st.set_page_config(page_title="Drug-Search Pro", layout="wide")

# 透過 URL 參數接收前端傳來的「生成請求」
query_params = st.query_params
if "action" in query_params and query_params["action"] == "generate":
    target_drug = query_params["name"]
    ai_generate_and_save(target_drug)
    # 生成後重置 URL
    st.query_params.clear()
    st.rerun()

# --- 4. 前端 UI (React + Firebase SDK) ---
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
</head>
<body class="bg-[#050a15] text-white">
    <div id="root"></div>
    <script type="text/babel">
        const {{ useState, useEffect }} = React;
        const firebaseConfig = {{
            apiKey: "AIzaSyDYzAXOd4xyJ5NOuwJl5nj7XgcVmba_54I",
            authDomain: "drug-search-pro.firebaseapp.com",
            projectId: "drug-search-pro",
            appId: "1:601449029455:web:d05d7592b32780efe86f3a"
        }};
        firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        const App = () => {{
            const [query, setQuery] = useState("");
            const [result, setResult] = useState(null);
            const [loading, setLoading] = useState(false);

            const search = async () => {{
                if (!query) return;
                setLoading(true);
                const name = query.trim().toUpperCase();
                
                try {{
                    const doc = await db.collection("med_knowledge").doc(name).get();
                    if (doc.exists) {{
                        setResult(doc.data().content);
                        setLoading(false);
                    }} else {{
                        // 🔴 關鍵：沒資料時，通知 Python 啟動 AI 生成
                        setResult("資料庫中無快取，正在透過 AI 自動生成數據，請稍候...");
                        window.parent.location.href = window.parent.location.origin + "?action=generate&name=" + name;
                    }}
                }} catch (e) {{
                    setResult("錯誤: " + e.message);
                    setLoading(false);
                }}
            }};

            return (
                <div className="p-10 max-w-4xl mx-auto">
                    <h1 className="text-3xl font-black mb-10 italic uppercase tracking-tighter">Drug-Search <span className="text-blue-500">PRO</span></h1>
                    <div className="bg-slate-900/50 p-2 rounded-2xl border border-blue-500/30 flex shadow-2xl">
                        <input 
                            className="bg-transparent flex-1 px-6 py-4 text-xl outline-none" 
                            placeholder="輸入藥名 (例如: CEFIN)..."
                            value={query}
                            onChange={{e => setQuery(e.target.value)}}
                            onKeyDown={{e => e.key === 'Enter' && search()}}
                        />
                        <button onClick={{search}} className="bg-blue-600 px-10 py-4 rounded-xl font-bold hover:bg-blue-500 transition-all">
                            {{loading ? "處理中..." : "檢索"}}
                        </button>
                    </div>
                    {{result && (
                        <div className="mt-10 p-10 bg-slate-900 rounded-3xl border border-blue-900/50 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="text-blue-500 text-xs font-bold mb-4 tracking-widest uppercase italic underline">Clinical Intelligence Data</div>
                            <pre className="whitespace-pre-wrap font-sans text-slate-300 leading-relaxed text-lg">{{result}}</pre>
                        </div>
                    )}}
                </div>
            );
        }};
        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>
"""

components.html(html_content, height=1000, scrolling=True)
