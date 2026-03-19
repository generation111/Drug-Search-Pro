import streamlit as st
import streamlit.components.v1 as components

# 1. 頁面基本配置
st.set_page_config(
    page_title="Rx Clinical Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 定義完整的 HTML/React/Firebase 程式碼
# ⚠️ 請在下方填入您的 API Key 與 Firebase 配置
html_content = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>臨床藥事快搜 Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
        body { font-family: 'Noto Sans TC', sans-serif; background-color: #F9FBFF; margin: 0; }
        .animate-in { animation: fadeIn 0.4s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .timer-pulse { animation: timerPulse 1.5s infinite; }
        @keyframes timerPulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;

        // --- 請填寫您的配置 ---
        const firebaseConfig = {
            apiKey: "您的_FIREBASE_API_KEY",
            authDomain: "您的專案.firebaseapp.com",
            projectId: "您的專案-ID",
            storageBucket: "您的專案.appspot.com",
            messagingSenderId: "您的ID",
            appId: "您的APP_ID"
        };
        
        const GEMINI_API_KEY = "您的_GEMINI_API_KEY";

        // 初始化 Firebase
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        const db = firebase.firestore();

        const App = () => {
            const [query, setQuery] = useState('');
            const [loading, setLoading] = useState(false);
            const [timer, setTimer] = useState(0);
            const [source, setSource] = useState('');
            const [result, setResult] = useState(null);
            const [cooldown, setCooldown] = useState(0);
            const timerRef = useRef(null);

            useEffect(() => {
                firebase.auth().signInAnonymously().catch(e => console.error(e));
            }, []);

            useEffect(() => {
                if (loading) {
                    setTimer(0);
                    timerRef.current = setInterval(() => setTimer(prev => prev + 0.1), 100);
                } else {
                    clearInterval(timerRef.current);
                }
                return () => clearInterval(timerRef.current);
            }, [loading]);

            useEffect(() => {
                if (cooldown > 0) {
                    const cdTimer = setTimeout(() => setCooldown(cooldown - 1), 1000);
                    return () => clearTimeout(cdTimer);
                }
            }, [cooldown]);

            const handleSearch = async (e) => {
                if (e) e.preventDefault();
                const q = query.trim().toUpperCase();
                if (!q || cooldown > 0) return;

                setLoading(true);
                setResult(null);
                try {
                    const docRef = db.collection("med_knowledge").doc(q);
                    const docSnap = await docRef.get();

                    if (docSnap.exists) {
                        setResult(docSnap.data().content);
                        setSource('Cloud Cache');
                    } else {
                        setSource('AI Search');
                        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                contents: [{ parts: [{ text: `請分析並引用台灣健保與臨床資料庫：${q}` }] }],
                                systemInstruction: { 
                                    parts: [{ text: `你是一位藥師。請分析藥品：1.【藥品基本資料】2.【臨床適應症與用法】3.【健保給付規定】4.【藥師臨床提示】。不使用粗體。` }] 
                                },
                                tools: [{ "google_search": {} }] 
                            })
                        });
                        const data = await response.json();
                        const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
                        if (text) {
                            const cleanedText = text.replace(/\\*\\*/g, '');
                            await docRef.set({ content: cleanedText, timestamp: firebase.firestore.FieldValue.serverTimestamp() });
                            setResult(cleanedText);
                            setCooldown(15);
                        }
                    }
                } catch (err) {
                    console.error(err);
                }
                setLoading(false);
            };

            return (
                <div className="max-w-4xl mx-auto p-4 md:p-8">
                    <header className="flex justify-between items-center mb-8">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold">Rx</div>
                            <h1 className="text-xl font-bold text-slate-800">Clinical <span className="text-indigo-600">Pro</span></h1>
                        </div>
                        <div className="text-xs font-mono text-slate-400">
                            {source} | {timer.toFixed(1)}s
                        </div>
                    </header>

                    {!result && !loading ? (
                        <form onSubmit={handleSearch} className="flex gap-2 p-2 bg-white rounded-2xl shadow-xl border">
                            <input 
                                className="flex-1 px-4 py-2 outline-none text-lg" 
                                placeholder={cooldown > 0 ? `冷卻中...${cooldown}` : "搜尋藥品..."}
                                value={query} 
                                onChange={e => setQuery(e.target.value)}
                                disabled={cooldown > 0}
                            />
                            <button className="bg-indigo-600 text-white px-6 py-2 rounded-xl font-bold">搜尋</button>
                        </form>
                    ) : loading ? (
                        <div className="text-center py-10 text-slate-400">正在連線資料庫...</div>
                    ) : (
                        <div className="bg-white rounded-3xl shadow-xl border overflow-hidden animate-in">
                            <div className="bg-slate-900 p-6 text-white flex justify-between">
                                <h2 className="text-2xl font-bold">{query}</h2>
                                <button onClick={() => {setResult(null); setQuery('');}} className="text-xs opacity-50">返回搜尋</button>
                            </div>
                            <div className="p-8 text-slate-700 whitespace-pre-wrap leading-relaxed">{result}</div>
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

# 3. 渲染組件
components.html(html_content, height=1000, scrolling=True)
