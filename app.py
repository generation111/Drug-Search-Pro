import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit.components.v1 as components

# --- 1. 後端 Firebase 初始化 (管理員權限) ---
if not firebase_admin._apps:
    try:
        # 如果您有 Service Account JSON，請放在 secrets 中
        if "firebase" in st.secrets:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
    except:
        pass

# --- 2. 頁面基本配置 ---
st.set_page_config(
    page_title="Drug-Search-Pro | Clinical Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. 前端 UI 與 Firebase Client 邏輯 ---
# 已加入自動啟用網路 (enableNetwork) 與更強健的錯誤處理
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
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fadeIn { animation: fadeIn 0.5s ease-out forwards; }
    </style>
</head>
<body>
    <div id="root" class="medical-grid min-h-screen"></div>

    <script type="text/babel">
        const { useState, useEffect } = React;

        // 核心配置 (俊林，這是根據您的截圖核對過的資訊)
        const firebaseConfig = {
            apiKey: "AIzaSyDYzAXOd4xyJ5NOuwJl5nj7XgcVmba_54I",
            authDomain: "drug-search-pro.firebaseapp.com",
            projectId: "drug-search-pro",
            storageBucket: "drug-search-pro.firebasestorage.app",
            messagingSenderId: "601449029455",
            appId: "1:601449029455:web:d05d7592b32780efe86f3a"
        };

        // 初始化 Firebase
        if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        // 關鍵修正：解決 "client is offline" 問題
        db.enableNetwork().catch((err) => console.error("網路啟用失敗", err));

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
                    // 執行資料庫查詢
                    const docRef = db.collection("med_knowledge").doc(drugName);
                    
                    // 強制從伺服器獲取最新資料，不使用快取
                    const docSnap = await docRef.get({ source: 'server' });

                    if (docSnap.exists) {
                        setResult(docSnap.data().content);
                    } else {
                        setResult("【臨床提醒】資料庫中尚未建立 " + drugName + " 的快取數據。\\n請確認 Firebase 集合名稱是否為 med_knowledge。");
                    }
                } catch (err) {
                    console.error("Firestore Error:", err);
                    setError("連線錯誤：" + err.message + " (請檢查 API Key 限制或網路環境)");
                }
                setLoading(false);
            };

            return (
                <div className="max-w-4xl mx-auto p-6 pt-16">
                    <header className="flex justify-between items-center mb-16">
                        <div className="flex items-center gap-4">
                            <div className="bg-blue-600 p-3 rounded-2xl shadow-lg">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                            </div>
                            <h1 className="text-2xl font-black uppercase italic tracking-tighter text-white">
                                Drug-Search <span className="text-blue-500 font-black">PRO</span>
                            </h1>
                        </div>
                    </header>

                    <main>
                        {!result && !loading ? (
                            <div className="animate-fadeIn space-y-8 text-center">
                                <div>
                                    <h2 className="text-4xl font-bold mb-4">藥學臨床智慧庫</h2>
                                    <p className="text-slate-400">請輸入藥品成分或商品名，系統將從 Firestore 提取結構化資料。</p>
                                </div>
                                <div className="glass-card p-2 flex border-blue-500/40 shadow-2xl max-w-2xl mx-auto">
                                    <input 
                                        className="bg-transparent flex-1 px-6 py-4 outline-none text-xl text-white placeholder:text-slate-700" 
                                        placeholder="例如: Holisoon"
                                        value={query}
                                        onChange={e => setQuery(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && searchDrug()}
                                    />
                                    <button onClick={searchDrug} className="bg-blue-600 hover:bg-blue-500 text-white px-10 py-4 rounded-2xl font-bold transition-all active:scale-95">
                                        檢索
                                    </button>
                                </div>
                            </div>
                        ) : loading ? (
                            <div className="py-24 text-center animate-pulse">
                                <div className="text-blue-500 text-xs font-mono tracking-[0.5em] mb-4 uppercase">Verifying Network Path...</div>
                                <div className="w-16 h-1 bg-blue-900/30 mx-auto rounded-full overflow-hidden">
                                    <div className="w-1/2 h-full bg-blue-500 animate-[loading_1.5s_infinite]"></div>
                                </div>
                            </div>
                        ) : (
                            <div className="animate-fadeIn space-y-6">
                                {error && (
                                    <div className="bg-red-900/20 border border-red-500/50 text-red-200 p-4 rounded-xl text-xs">
                                        ⚠️ {error}
                                    </div>
                                )}
                                <div className="glass-card overflow-hidden shadow-2xl">
                                    <div className="bg-blue-600/10 p-8 border-b border-blue-900/20">
                                        <div className="text-blue-500 text-[10px] font-bold tracking-widest uppercase mb-1">Result Found</div>
                                        <h2 className="text-4xl font-black text-white">{query}</h2>
                                    </div>
                                    <div className="p-10 text-slate-300 text-lg leading-relaxed whitespace-pre-wrap font-light">
                                        {result}
                                    </div>
                                </div>
                                <button onClick={() => {setResult(null); setQuery("");}} className="text-slate-500 hover:text-blue-400 font-bold text-sm flex items-center gap-2">
                                    ← 返回重新查詢
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
    <style>
        @keyframes loading { from { transform: translateX(-100%); } to { transform: translateX(200%); } }
    </style>
</body>
</html>
"""

# --- 4. 渲染 ---
components.html(html_content, height=1000, scrolling=True)
