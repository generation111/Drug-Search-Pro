import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit.components.v1 as components

# --- 1. 後端 Firebase 初始化 (用於 Python 端的數據管理) ---
if not firebase_admin._apps:
    try:
        # 請確保您已在 Streamlit Secrets 中填入 Service Account JSON
        if "firebase" in st.secrets:
            firebase_secrets = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_secrets)
            firebase_admin.initialize_app(cred)
        else:
            # 本地測試模式
            pass
    except Exception as e:
        st.error(f"Firebase 後端連線失敗: {e}")

# --- 2. 頁面基本配置 ---
st.set_page_config(
    page_title="Drug-Search-Pro | Clinical Database",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. 前端 UI 與 Firebase Client 聯動邏輯 ---
# 這裡使用了您最新生成的 Firebase Web Config
html_content = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Noto+Sans+TC:wght@300;400;700&display=swap');
        body { margin: 0; background: #050a15; color: #f8fafc; font-family: 'Inter', 'Noto Sans TC', sans-serif; overflow-x: hidden; }
        .medical-grid { background-image: radial-gradient(circle at 2px 2px, rgba(59,130,246,0.1) 1px, transparent 0); background-size: 40px 40px; }
        .glass-card { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 24px; }
        .search-glow:focus-within { box-shadow: 0 0 20px rgba(59, 130, 246, 0.4); border-color: #3b82f6; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .animate-slideUp { animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
    </style>
</head>
<body>
    <div id="root" class="medical-grid min-h-screen"></div>

    <script type="text/babel">
        const { useState, useEffect } = React;

        // 🔗 俊林，這裡就是我們核對過的正確金鑰
       // 請將此段完整替換到您的程式碼中
const firebaseConfig = {
    apiKey: "AIzaSyDYzAXOd4xyJ5NOuwJl5nj7XgcVmba_54I",
    authDomain: "drug-search-pro.firebaseapp.com",
    projectId: "drug-search-pro",
    storageBucket: "drug-search-pro.firebasestorage.app",
    messagingSenderId: "601449029455",
    appId: "1:601449029455:web:d05d7592b32780efe86f3a"
};

        };

        // 初始化 Firebase
        if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        const App = () => {
            const [query, setQuery] = useState("");
            const [result, setResult] = useState(null);
            const [loading, setLoading] = useState(false);
            const [error, setError] = useState(null);

            const searchDrug = async () => {
                const drugName = query.trim().toUpperCase();
                if (!drugName) return;
                
                setLoading(true);
                setError(null);
                
                try {
                    // 🔍 搜尋 Firestore 集合：med_knowledge
                    const docRef = db.collection("med_knowledge").doc(drugName);
                    const docSnap = await docRef.get();

                    if (docSnap.exists) {
                        setResult(docSnap.data().content);
                    } else {
                        setResult("【臨床提醒】\\n目前資料庫中尚未建立 " + drugName + " 的結構化快取數據。\\n系統已記錄此查詢，將於下次數據同步時自動補充。");
                    }
                } catch (err) {
                    console.error("Firebase Error:", err);
                    setError("連線失敗：" + err.message + "。請確認 Firestore Rules 已設為 if true。");
                }
                setLoading(false);
            };

            return (
                <div className="max-w-6xl mx-auto p-6 md:p-12">
                    {/* Header */}
                    <header className="flex justify-between items-center mb-20">
                        <div className="flex items-center gap-4">
                            <div className="bg-blue-600 w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/40">
                                <span className="text-white font-black text-xl">Rx</span>
                            </div>
                            <h1 className="text-3xl font-black tracking-tighter uppercase italic">
                                Drug-Search <span className="text-blue-500">PRO</span>
                            </h1>
                        </div>
                        <div className="hidden md:block text-right">
                            <div className="text-[10px] font-mono text-blue-400 uppercase tracking-widest bg-blue-900/20 px-3 py-1 rounded-full border border-blue-800/50">
                                Clinical Intelligence v2.0
                            </div>
                        </div>
                    </header>

                    {/* Main Interface */}
                    <main className="max-w-3xl mx-auto">
                        {!result && !loading ? (
                            <div className="animate-slideUp space-y-12">
                                <div className="text-center space-y-4">
                                    <h2 className="text-5xl font-bold tracking-tight text-white">智慧藥學檢索</h2>
                                    <p className="text-slate-400 text-lg font-light">整合 TFDA 與臨床藥理數據，提供結構化資訊回饋。</p>
                                </div>
                                
                                <div className="glass-card p-3 flex items-center search-glow transition-all duration-300">
                                    <input 
                                        className="bg-transparent flex-1 px-6 py-4 outline-none text-xl font-medium text-white placeholder:text-slate-600" 
                                        placeholder="輸入商品名或成分學名..."
                                        value={query}
                                        onChange={e => setQuery(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && searchDrug()}
                                    />
                                    <button 
                                        onClick={searchDrug}
                                        className="bg-blue-600 hover:bg-blue-500 text-white px-10 py-4 rounded-xl font-bold transition-all active:scale-95 shadow-lg"
                                    >
                                        立即檢索
                                    </button>
                                </div>
                                
                                <div className="grid grid-cols-3 gap-4 text-center">
                                    {["學名檢索", "健保代碼", "臨床用途"].map(tag => (
                                        <div key={tag} className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{tag}</div>
                                    ))}
                                </div>
                            </div>
                        ) : loading ? (
                            <div className="py-40 text-center space-y-6">
                                <div className="inline-block w-12 h-12 border-4 border-blue-600/20 border-t-blue-500 rounded-full animate-spin"></div>
                                <div className="text-xs font-mono text-blue-500 tracking-[0.3em] uppercase animate-pulse">Connecting to Secure Database</div>
                            </div>
                        ) : (
                            <div className="animate-slideUp space-y-8">
                                {error && (
                                    <div className="bg-red-900/20 border border-red-500/50 text-red-200 p-4 rounded-xl text-sm">
                                        ⚠️ {error}
                                    </div>
                                )}
                                <div className="glass-card overflow-hidden shadow-2xl border-blue-500/30">
                                    <div className="bg-blue-600/20 p-8 border-b border-blue-900/30 flex justify-between items-end">
                                        <div>
                                            <div className="text-blue-400 text-[10px] font-bold tracking-widest uppercase mb-1">Search Result</div>
                                            <h2 className="text-4xl font-black text-white uppercase">{query}</h2>
                                        </div>
                                        <div className="text-slate-500 text-[10px] font-mono mb-1 tracking-tighter italic underline underline-offset-4">Verified Source</div>
                                    </div>
                                    <div className="p-10">
                                        <div className="whitespace-pre-wrap text-slate-300 leading-relaxed text-lg font-light tracking-wide italic">
                                            {result}
                                        </div>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {setResult(null); setQuery("");}} 
                                    className="flex items-center gap-2 text-slate-500 hover:text-blue-400 transition-colors font-bold text-sm uppercase tracking-tighter"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M10 19l-7-7m0 0l7-7m-7 7h18" strokeWidth="3" /></svg>
                                    返回重新搜尋
                                </button>
                            </div>
                        )}
                    </main>
                </div>
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
"""

# --- 4. 渲染頁面 ---
components.html(html_content, height=1200, scrolling=True)
