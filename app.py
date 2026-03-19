<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>臨床藥事快搜 Pro - Firestore 集成版</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
        body { font-family: 'Noto Sans TC', sans-serif; background-color: #F9FBFF; }
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

        // --- [修正重點 1]：Firebase 配置 ---
        const firebaseConfig = {
            apiKey: "您的_FIREBASE_API_KEY",
            authDomain: "您的專案.firebaseapp.com",
            projectId: "您的專案-ID",
            storageBucket: "您的專案.appspot.com",
            messagingSenderId: "您的ID",
            appId: "您的APP_ID"
        };
        
        // 初始化 Firebase
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        const db = firebase.firestore();

        // --- [修正重點 2]：Gemini 配置 ---
        const GEMINI_API_KEY = "您的_GEMINI_API_KEY";

        const App = () => {
            const [query, setQuery] = useState('');
            const [loading, setLoading] = useState(false);
            const [timer, setTimer] = useState(0);
            const [source, setSource] = useState(''); // 'Cloud Cache' or 'AI Search'
            const [result, setResult] = useState(null);
            const [cooldown, setCooldown] = useState(0); // [修正重點 3] 冷卻時間
            const timerRef = useRef(null);

            // 匿名登入
            useEffect(() => {
                firebase.auth().signInAnonymously().catch(e => console.error("Auth Error", e));
            }, []);

            // 計時器邏輯
            useEffect(() => {
                if (loading) {
                    setTimer(0);
                    timerRef.current = setInterval(() => setTimer(prev => prev + 0.1), 100);
                } else {
                    clearInterval(timerRef.current);
                }
                return () => clearInterval(timerRef.current);
            }, [loading]);

            // [修正重點 4] 冷卻倒數計時器
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
                setSource('');

                try {
                    // --- [核心邏輯]：先讀取 Firestore 雲端快取 ---
                    const docRef = db.collection("med_knowledge").doc(q);
                    const docSnap = await docRef.get();

                    if (docSnap.exists) {
                        // 雲端有資料，直接使用
                        setResult(docSnap.data().content);
                        setSource('Cloud Cache (Verified)');
                    } else {
                        // 雲端無資料，調用 Gemini AI 並連網搜尋
                        setSource('Global AI Search');
                        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                contents: [{ parts: [{ text: `請分析並引用台灣健保與臨床資料庫：${q}` }] }],
                                systemInstruction: { 
                                    parts: [{ 
                                        text: `你是一位資深臨床藥師。請針對藥品進行專業分析：
                                        1. 必須引用：台灣食藥署(TFDA)許可證、健保署(NHI)代碼與給付規範。
                                        2. 結構：
                                           - 【藥品基本資料】：成分、商品名、健保代碼與單價。
                                           - 【臨床適應症與用法】：TFDA核准用途、建議劑量。
                                           - 【健保給付規定】：是否有特殊規定。
                                           - 【藥師臨床提示】：重大副作用、配製注意事項。
                                        3. 嚴禁使用粗體 (**)，內容清晰分段。` 
                                    }] 
                                },
                                tools: [{ "google_search": {} }] 
                            })
                        });

                        const data = await response.json();
                        
                        // 處理 429 報錯
                        if (data.error && data.error.code === 429) {
                            throw new Error("429_LIMIT");
                        }

                        const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
                        if (text) {
                            const cleanedText = text.replace(/\*\*/g, '');
                            // --- [核心邏輯]：存入 Firestore 供全體共享 ---
                            await docRef.set({
                                content: cleanedText,
                                timestamp: firebase.firestore.FieldValue.serverTimestamp(),
                                search_count: 1
                            });
                            setResult(cleanedText);
                            // 搜尋成功，進入 15 秒保護冷卻
                            setCooldown(15);
                        }
                    }
                } catch (err) {
                    if (err.message === "429_LIMIT") {
                        alert("⚠️ API 流量限制中，請稍候 30 秒再試，或嘗試搜尋其他藥品。");
                        setCooldown(30);
                    } else {
                        console.error("Search Error:", err);
                    }
                }
                setLoading(false);
            };

            const resetSearch = () => { setResult(null); setQuery(''); setCooldown(0); };

            return (
                <div className="max-w-4xl mx-auto p-6 md:p-12 pb-32">
                    <header className="flex justify-between items-center mb-12">
                        <div className="flex items-center gap-3 cursor-pointer" onClick={resetSearch}>
                            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-black italic shadow-lg">Rx</div>
                            <h1 className="text-2xl font-black tracking-tight text-slate-800">Clinical <span className="text-indigo-600">Pro</span></h1>
                        </div>
                        <div className={`px-4 py-2 rounded-full border bg-white shadow-sm font-mono text-xs ${loading ? 'timer-pulse text-indigo-600 border-indigo-200' : 'text-slate-400'}`}>
                            {source ? `${source} | ${timer.toFixed(1)}s` : `${timer.toFixed(1)}s`}
                        </div>
                    </header>

                    {!result && !loading ? (
                        <div className="animate-in">
                            <form onSubmit={handleSearch} className="flex gap-2 p-2 bg-white rounded-3xl shadow-2xl border border-slate-100">
                                <input 
                                    className="flex-1 px-6 py-4 outline-none text-xl font-bold" 
                                    placeholder={cooldown > 0 ? `請稍候 ${cooldown} 秒...` : "輸入藥品關鍵字..."}
                                    value={query} 
                                    onChange={e => setQuery(e.target.value)}
                                    disabled={cooldown > 0}
                                />
                                <button 
                                    disabled={cooldown > 0}
                                    className={`${cooldown > 0 ? 'bg-slate-300' : 'bg-indigo-600 hover:bg-indigo-700'} text-white px-8 rounded-2xl font-black transition-all`}
                                >
                                    {cooldown > 0 ? `${cooldown}s` : '搜尋'}
                                </button>
                            </form>
                            <p className="mt-4 text-center text-slate-400 text-sm">支援所有健保藥品檢索，檢索結果將自動存入雲端資料庫</p>
                        </div>
                    ) : loading ? (
                        <div className="text-center py-20">
                            <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-slate-400 font-bold tracking-widest text-sm uppercase">正在存取雲端資料庫與食藥署數據...</p>
                        </div>
                    ) : (
                        <div className="animate-in">
                            <div className="flex justify-between items-center mb-6">
                                <button onClick={resetSearch} className="text-slate-400 font-bold hover:text-indigo-600">← 返回搜尋</button>
                                <span className="bg-green-50 text-green-600 px-3 py-1 rounded-md text-[10px] font-bold border border-green-100">檢索成功</span>
                            </div>
                            <div className="bg-white rounded-[2.5rem] shadow-2xl border border-slate-100 overflow-hidden">
                                <div className="bg-slate-900 px-10 py-8 text-white flex justify-between items-end">
                                    <div>
                                        <h2 className="text-3xl font-black">{query}</h2>
                                        <p className="text-slate-400 text-[10px] mt-2 tracking-widest uppercase">Clinical Grounding Mode</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-slate-500 text-[10px] uppercase font-bold">Source</p>
                                        <p className="text-xs font-mono">{source}</p>
                                    </div>
                                </div>
                                <div className="p-10 text-lg leading-relaxed text-slate-700 whitespace-pre-wrap">
                                    {result}
                                </div>
                            </div>
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
