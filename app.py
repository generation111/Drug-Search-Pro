import streamlit as st
import streamlit.components.v1 as components

# 1. 頁面基本配置
st.set_page_config(
    page_title="Rx Clinical Pro Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 將您的 React 程式碼封裝進 HTML 字串
# 注意：我已經幫您處理了 JavaScript 中的反引號與標點符號，使其在 Python 字串中安全運行
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
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
        body { margin: 0; padding: 0; overflow-x: hidden; }
        @keyframes cfadeup { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        @keyframes cpulse  { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes cspin   { to{transform:rotate(360deg)} }
        @keyframes cspinr  { from{transform:translate(-50%,-50%) rotate(0)} to{transform:translate(-50%,-50%) rotate(-360deg)} }
        * { box-sizing:border-box; }
        ::-webkit-scrollbar { width:5px; }
        ::-webkit-scrollbar-track { background:#08101f; }
        ::-webkit-scrollbar-thumb { background:#1e293b; border-radius:99px; }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;

        const QUICK_TAGS = ["Metformin", "Amoxicillin", "Warfarin", "Atorvastatin", "Omeprazole", "Lisinopril", "Aspirin", "Amlodipine"];
        const LOADING_STEPS = ["查詢台灣食藥署 TFDA 資料庫...", "比對健保署 NHI 給付規範...", "搜尋臨床藥理資訊...", "整合分析報告中..."];
        const SECTIONS = ["藥品基本資料", "臨床適應症與用法", "健保給付規定", "藥師臨床提示"];
        const SECTION_ICONS = { "藥品基本資料": "💊", "臨床適應症與用法": "📋", "健保給付規定": "🏥", "藥師臨床提示": "⚠️" };

        // ⚠️ 請填入您的 ANTHROPIC 或 GEMINI API KEY
        const API_KEY = "您的_API_KEY_在此";

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
                const nexts = SECTIONS.map((s) => rem.indexOf(`【${s}】`)).filter((i) => i > 0).sort((a, b) => a - b);
                const end = nexts[0];
                blocks.push({ title: sec, content: end !== undefined ? rem.slice(0, end).trim() : rem.trim() });
                if (end !== undefined) rem = rem.slice(end);
            }
            return blocks.length ? blocks : [{ title: null, content: cleaned.trim() }];
        }

        const App = () => {
            const [query, setQuery] = useState("");
            const [loading, setLoading] = useState(false);
            const [timer, setTimer] = useState(0);
            const [isCached, setIsCached] = useState(false);
            const [result, setResult] = useState(null);
            const [activeStep, setActiveStep] = useState(0);
            const timerRef = useRef(null);
            const cache = useRef({});

            useEffect(() => {
                if (loading) {
                    timerRef.current = setInterval(() => setTimer((p) => +(p + 0.1).toFixed(1)), 100);
                } else {
                    clearInterval(timerRef.current);
                }
                return () => clearInterval(timerRef.current);
            }, [loading]);

            const search = async (q = query) => {
                const t = q.trim();
                if (!t) return;
                if (cache.current[t]) {
                    setIsCached(true); setResult(cache.current[t]); setLoading(false); return;
                }
                setIsCached(false); setLoading(true); setResult(null);
                
                try {
                    // 這裡預設使用您程式碼中的 Anthropic 結構，如果是用 Gemini 請自行替換 URL
                    const res = await fetch("https://api.anthropic.com/v1/messages", {
                        method: "POST",
                        headers: {
                            "content-type": "application/json",
                            "x-api-key": API_KEY,
                            "anthropic-version": "2023-06-01",
                            "anthropic-dangerous-direct-browser-access": "true",
                        },
                        body: JSON.stringify({
                            model: "claude-3-5-sonnet-20240620",
                            max_tokens: 1500,
                            system: SYS,
                            messages: [{ role: "user", content: `請分析：${t}` }],
                        }),
                    });
                    const json = await res.json();
                    const text = json.content[0].text;
                    cache.current[t] = text;
                    setResult(text);
                } catch (e) { alert("查詢出錯，請檢查 API Key"); }
                setLoading(false);
            };

            const blocks = result ? parseResult(result) : [];

            return (
                <div style={{ minHeight: "100vh", background: "#08101f", color: "#e2e8f0", fontFamily: "'Noto Sans TC', sans-serif" }}>
                    <header style={{ padding: "18px 32px", borderBottom: "1px solid rgba(99,179,237,0.1)", display: "flex", justifyContent: "space-between", background: "rgba(8,16,31,0.9)", backdropFilter: "blur(10px)", sticky: "top" }}>
                        <div style={{ fontWeight: 900, display: "flex", alignItems: "center", gap: 10 }}>
                            <div style={{ background: "#4f9cf9", padding: "4px 8px", borderRadius: 6 }}>Rx</div>
                            <span>Clinical Pro</span>
                        </div>
                        <div style={{ fontSize: 12, opacity: 0.6 }}>{timer.toFixed(1)}s</div>
                    </header>

                    <main style={{ maxWidth: 800, margin: "0 auto", padding: "60px 20px" }}>
                        {!result && !loading ? (
                            <div style={{ animation: "cfadeup 0.5s forwards" }}>
                                <h1 style={{ textAlign: "center", fontSize: 40, fontWeight: 900, marginBottom: 40 }}>藥事快搜 <span style={{ color: "#4f9cf9" }}>Pro</span></h1>
                                <div style={{ display: "flex", background: "#111827", borderRadius: 16, border: "1px solid #1e293b", overflow: "hidden" }}>
                                    <input 
                                        style={{ flex: 1, padding: 20, background: "none", border: "none", color: "#fff", outline: "none" }} 
                                        placeholder="輸入藥品名稱..." 
                                        value={query}
                                        onChange={e => setQuery(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && search()}
                                    />
                                    <button onClick={() => search()} style={{ background: "#4f9cf9", color: "#fff", padding: "0 30px", fontWeight: "bold" }}>搜尋</button>
                                </div>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 20, justifyContent: "center" }}>
                                    {QUICK_TAGS.map(tag => (
                                        <button key={tag} onClick={() => search(tag)} style={{ fontSize: 12, background: "#111827", border: "1px solid #1e293b", padding: "6px 12px", borderRadius: 8 }}>{tag}</button>
                                    ))}
                                </div>
                            </div>
                        ) : loading ? (
                            <div style={{ textAlign: "center", padding: 100 }}>
                                <div style={{ width: 50, height: 50, border: "3px solid #1e293b", borderTopColor: "#4f9cf9", borderRadius: "50%", animation: "cspin 1s linear infinite", margin: "0 auto 20px" }}></div>
                                <p style={{ color: "#4f9cf9", fontSize: 14 }}>正在調研專業資料庫...</p>
                            </div>
                        ) : (
                            <div style={{ animation: "cfadeup 0.5s forwards" }}>
                                <button onClick={() => {setResult(null); setQuery("");}} style={{ marginBottom: 20, opacity: 0.5 }}>← 返回</button>
                                <div style={{ background: "#111827", borderRadius: 24, border: "1px solid #1e293b", overflow: "hidden" }}>
                                    <div style={{ background: "#1e293b", padding: "20px 30px" }}>
                                        <h2 style={{ fontSize: 24, fontWeight: 900 }}>{query}</h2>
                                    </div>
                                    <div style={{ padding: 30 }}>
                                        {blocks.map((b, i) => (
                                            <div key={i} style={{ marginBottom: 30 }}>
                                                <div style={{ color: "#4f9cf9", fontWeight: "bold", marginBottom: 10 }}>{SECTION_ICONS[b.title]} {b.title}</div>
                                                <div style={{ whiteSpace: "pre-wrap", color: "#94a3b8", fontSize: 15, lineHeight: 1.8 }}>{b.content}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
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

# 3. 使用 Streamlit 元件顯示
components.html(html_content, height=1000, scrolling=True)
