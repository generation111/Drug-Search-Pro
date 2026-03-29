import streamlit as st
import streamlit.components.v1 as components

# 1. 頁面基本配置
st.set_page_config(
    page_title="Rx Clinical Pro Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 定義完整 HTML/JS/Firebase 邏輯
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
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
        body { margin: 0; background: #08101f; color: #e2e8f0; font-family: 'Noto Sans TC', sans-serif; }
        @keyframes cfadeup { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        @keyframes cspin { to{transform:rotate(360deg)} }
        .grid-bg { background-image: linear-gradient(rgba(79,156,249,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,156,249,0.04) 1px,transparent 1px); background-size: 40px 40px; }
    </style>
</head>
<body>
    <div id="root" class="grid-bg min-h-screen"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;

        // --- ⚠️ 配置區 ---
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
        if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        const QUICK_TAGS = ["Metformin", "Amoxicillin", "Warfarin", "Atorvastatin", "Omeprazole", "Lisinopril", "Aspirin", "Amlodipine"];
        const SECTIONS = ["藥品基本資料", "臨床適應症與用法", "健保給付規定", "藥師臨床提示"];
        const SECTION_ICONS = { "藥品基本資料": "💊", "臨床適應症與用法": "📋", "健保給付規定": "🏥", "藥師臨床提示": "⚠️" };

        const SYS = `你是一位資深臨床藥師，專精台灣健保與臨床藥學。請針對查詢的藥品進行專業分析，並嚴格使用以下四個標題結構：
【藥品基本資料】
列出：成分（INN名稱）、常見商品名、劑型規格、台灣健保代碼與點數。
【臨床適應症與用法】
列出：TFDA核准適應症、標準建議劑量、給藥途徑、特殊族群劑量調整。
【健保給付規定】
列出：是否為健保給付、是否需事前審查、開立限制。
【藥師臨床提示】
列出：重要藥物交互作用、重大副作用警示、病患衛教重點。
請以繁體中文回答，條列清晰，不要使用粗體語法。`;

        function parseResult(text) {
            const cleaned = text.replace(/\\*\\*/g, "");
            const blocks = [];
            let rem = cleaned;
            for (const sec of SECTIONS) {
                const marker = `【${sec}】`;
                const idx = rem.indexOf(marker);
                if (idx === -1) continue;
                rem = rem.slice(idx + marker.length);
                const nexts = SECTIONS.map(s => rem.indexOf(`【${s}】`)).filter(i => i > 0).sort((a,b) => a-b);
                const end = nexts[0];
                blocks.push({ title: sec, content: end !== undefined ? rem.slice(0, end).trim() : rem.trim() });
                if (end !== undefined) rem = rem.slice(end);
            }
            return blocks.length ? blocks : [{ title: null, content: cleaned.trim() }];
        }

        const App = () => {
            const [query, setQuery] = useState("");
            const [loading, setLoading] = useState(false);
            const [result, setResult] = useState(null);
            const [source, setSource] = useState("");
            const [timer, setTimer] = useState(0);
            const timerRef = useRef(null);

            useEffect(() => {
                firebase.auth().signInAnonymously().catch(console.error);
            }, []);

            const search = async (q = query) => {
                const t = q.trim().toUpperCase();
                if (!t) return;
                setLoading(true); setResult(null); setTimer(0);
                timerRef.current = setInterval(() => setTimer(p => +(p+0.1).toFixed(1)), 100);

                try {
                    // 1. 檢查 Firestore 快取
                    const docRef = db.collection("med_knowledge").doc(t);
                    const docSnap = await docRef.get();

                    if (docSnap.exists) {
                        setResult(docSnap.data().content);
                        setSource("Cloud Cache");
                    } else {
                        // 2. 調用 Gemini API (Google Search 模式)
                        setSource("Gemini AI Search");
                        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                contents: [{ parts: [{ text: `請分析：${t}` }] }],
                                systemInstruction: { parts: [{ text: SYS }] },
                                tools: [{ "google_search": {} }]
                            })
                        });
                        const data = await res.json();
                        const text = data.candidates[0].content.parts[0].text;
                        
                        // 3. 儲存至 Firestore
                        await docRef.set({
                            content: text,
                            timestamp: firebase.firestore.FieldValue.serverTimestamp()
                        });
                        setResult(text);
                    }
                } catch (e) {
                    alert("錯誤：" + (e.message || "請檢查 API Key 或網路連線"));
                }
                clearInterval(timerRef.current);
                setLoading(false);
            };

            const blocks = result ? parseResult(result) : [];

            return (
                <div className="p-4 md:p-8">
                    <header className="max-w-4xl mx-auto flex justify-between items-center mb-12">
                        <div className="flex items-center gap-3 cursor-pointer" onClick={() => {setResult(null); setQuery("");}}>
                            <div className="bg-blue-600 w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/30">Rx</div>
                            <h1 className="text-xl font-black italic">CLINICAL <span className="text-blue-500">PRO</span></h1>
                        </div>
                        <div className="text-xs font-mono opacity-40">{source} {timer}s</div>
                    </header>

                    <main className="max-w-3xl mx-auto">
                        {!result && !loading ? (
                            <div className="animate-[cfadeup_0.5s]">
                                <div className="bg-[#111827] border border-blue-900/30 p-2 rounded-2xl flex shadow-2xl">
                                    <input 
                                        className="bg-transparent flex-1 px-4 py-3 outline-none font-bold text-lg" 
                                        placeholder="輸入學名或商品名..."
                                        value={query}
                                        onChange={e => setQuery(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && search()}
                                    />
                                    <button onClick={() => search()} className="bg-blue-600 px-8 rounded-xl font-bold hover:bg-blue-500 transition-colors">搜尋</button>
                                </div>
                                <div className="flex flex-wrap gap-2 mt-6 justify-center">
                                    {QUICK_TAGS.map(tag => (
                                        <button key={tag} onClick={() => search(tag)} className="text-xs bg-[#111827] border border-slate-800 px-3 py-1.5 rounded-lg opacity-60 hover:opacity-100 hover:border-blue-500">{tag}</button>
                                    ))}
                                </div>
                            </div>
                        ) : loading ? (
                            <div className="text-center py-24">
                                <div className="w-12 h-12 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-[cspin_1s_linear_infinite] mx-auto mb-6"></div>
                                <p className="text-blue-400 font-mono text-sm tracking-widest">RESEARCHING DATABASE...</p>
                            </div>
                        ) : (
                            <div className="animate-[cfadeup_0.5s]">
                                <div className="bg-[#111827] border border-blue-900/20 rounded-3xl overflow-hidden shadow-2xl">
                                    <div className="bg-gradient-to-r from-blue-900/20 to-transparent p-8 border-b border-blue-900/10">
                                        <h2 className="text-3xl font-black tracking-tight">{query}</h2>
                                    </div>
                                    <div className="p-8 space-y-10">
                                        {blocks.map((b, i) => (
                                            <div key={i}>
                                                <div className="text-blue-500 text-xs font-black tracking-widest mb-3 uppercase flex items-center gap-2">
                                                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                                                    {SECTION_ICONS[b.title]} {b.title}
                                                </div>
                                                <div className="text-slate-400 leading-relaxed text-sm whitespace-pre-wrap">{b.content}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <button onClick={() => {setResult(null); setQuery("");}} className="mt-8 text-slate-600 hover:text-blue-400 text-sm font-bold transition-colors">← 返回重新搜尋</button>
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

# 3. 渲染
components.html(html_content, height=1200, scrolling=True)
