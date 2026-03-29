import streamlit as st
import streamlit.components.v1 as components

# --- 1. 後端 Firebase 初始化 (嘗試性載入) ---
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    if not firebase_admin._apps:
        # 檢查是否有 Secret 設定，若無則跳過後端初始化
        if "firebase" in st.secrets:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
except ImportError:
    # 如果雲端還沒安裝好 firebase-admin，先不報錯，讓前端 HTML 跑起來
    pass

# --- 2. 頁面基本配置 ---
st.set_page_config(
    page_title="Drug-Search-Pro | Clinical Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. 前端 UI 與 Firebase Client 邏輯 ---
html_content = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Noto+Sans+TC:wght@300;400;700&display=swap');
        body { margin: 0; background: #050a15; color: #f8fafc; font-family: 'Inter', 'Noto Sans TC', sans-serif; }
        .medical-grid { background-image: radial-gradient(circle at 2px 2px, rgba(59,130,246,0.1) 1px, transparent 0); background-size: 40px 40px; }
        .glass-card { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 28px; }
    </style>
</head>
<body>
    <div id="root" class="medical-grid min-h-screen"></div>
    <script type="text/babel">
        const { useState } = React;
        const firebaseConfig = {
            apiKey: "AIzaSyDYzAXOd4xyJ5NOuwJl5nj7XgcVmba_54I",
            authDomain: "drug-search-pro.firebaseapp.com",
            projectId: "drug-search-pro",
            storageBucket: "drug-search-pro.firebasestorage.app",
            messagingSenderId: "601449029455",
            appId: "1:601449029455:web:d05d7592b32780efe86f3a"
        };

        if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();
        db.enableNetwork().catch(console.error);

        const App = () => {
            const [query, setQuery] = useState("");
            const [result, setResult] = useState(null);
            const [loading, setLoading] = useState(false);

            const searchDrug = async () => {
                const drugName = query.trim().toUpperCase();
                if (!drugName) return;
                setLoading(true);
                try {
                    const docSnap = await db.collection("med_knowledge").doc(drugName).get({ source: 'server' });
                    setResult(docSnap.exists ? docSnap.data().content : "尚未建立 " + drugName + " 的快取數據。");
                } catch (err) {
                    setResult("連線錯誤：" + err.message);
                }
                setLoading(false);
            };

            return (
                <div className="max-w-4xl mx-auto p-6 pt-16">
                    <h1 className="text-2xl font-black uppercase italic text-white mb-10">Drug-Search <span className="text-blue-500">PRO</span></h1>
                    {!result && !loading ? (
                        <div className="space-y-6 text-center">
                            <h2 className="text-4xl font-bold">藥學臨床智慧庫</h2>
                            <div className="glass-card p-2 flex max-w-2xl mx-auto border-blue-500/40">
                                <input className="bg-transparent flex-1 px-6 py-4 text-white outline-none" placeholder="輸入藥名..." value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && searchDrug()}/>
                                <button onClick={searchDrug} className="bg-blue-600 px-10 py-4 rounded-2xl font-bold">檢索</button>
                            </div>
                        </div>
                    ) : loading ? (
                        <div className="text-center py-20 text-blue-500 animate-pulse uppercase tracking-widest">Searching Database...</div>
                    ) : (
                        <div className="glass-card p-10 space-y-6">
                            <h2 className="text-3xl font-black text-blue-500">{query}</h2>
                            <p className="text-slate-300 whitespace-pre-wrap">{result}</p>
                            <button onClick={() => {setResult(null); setQuery("");}} className="text-slate-500 hover:text-white">← 返回</button>
                        </div>
                    )}
                </div>
            );
        };
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
"""

components.html(html_content, height=1000, scrolling=True)
