import { useState, useEffect, useRef } from "react";

const QUICK_TAGS = ["Metformin", "Amoxicillin", "Warfarin", "Atorvastatin", "Omeprazole", "Lisinopril", "Aspirin", "Amlodipine"];

const LOADING_STEPS = [
  "查詢台灣食藥署 TFDA 資料庫...",
  "比對健保署 NHI 給付規範...",
  "搜尋臨床藥理資訊...",
  "整合分析報告中...",
];

const SECTIONS = ["藥品基本資料", "臨床適應症與用法", "健保給付規定", "藥師臨床提示"];
const SECTION_ICONS = {
  "藥品基本資料": "💊",
  "臨床適應症與用法": "📋",
  "健保給付規定": "🏥",
  "藥師臨床提示": "⚠️",
};

const SYS = `你是一位資深臨床藥師，專精台灣健保與臨床藥學。請針對查詢的藥品進行專業分析，並嚴格使用以下四個標題結構：

【藥品基本資料】
列出：成分（INN名稱）、常見商品名、劑型規格、台灣健保代碼與點數。

【臨床適應症與用法】
列出：TFDA核准適應症、標準建議劑量、給藥途徑、特殊族群（腎功能不全、老年人）劑量調整。

【健保給付規定】
列出：是否為健保給付、是否需事前審查、開立限制（如限定科別）、自費事項。

【藥師臨床提示】
列出：重要藥物交互作用、重大副作用警示、配製或儲存注意事項、病患衛教重點。

請以繁體中文回答，語氣專業嚴謹，條列清晰。不要使用 **粗體** Markdown 語法。`;

function parseResult(text) {
  const cleaned = text.replace(/\*\*/g, "");
  const blocks = [];
  let rem = cleaned;
  for (const sec of SECTIONS) {
    const marker = `【${sec}】`;
    const idx = rem.indexOf(marker);
    if (idx === -1) continue;
    if (idx > 0) {
      const pre = rem.slice(0, idx).trim();
      if (pre) blocks.push({ title: null, content: pre });
    }
    rem = rem.slice(idx + marker.length);
    const nexts = SECTIONS.map((s) => rem.indexOf(`【${s}】`)).filter((i) => i > 0).sort((a, b) => a - b);
    const end = nexts[0];
    blocks.push({ title: sec, content: end !== undefined ? rem.slice(0, end).trim() : rem.trim() });
    if (end !== undefined) rem = rem.slice(end);
    else { rem = ""; break; }
  }
  if (rem.trim()) blocks.push({ title: null, content: rem.trim() });
  if (!blocks.length) blocks.push({ title: null, content: cleaned.trim() });
  return blocks;
}

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(0);
  const [isCached, setIsCached] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const timerRef = useRef(null);
  const stepRef = useRef(null);
  const cache = useRef({});

  useEffect(() => {
    if (loading) {
      setTimer(0); setActiveStep(0);
      timerRef.current = setInterval(() => setTimer((p) => +(p + 0.1).toFixed(1)), 100);
      stepRef.current = setInterval(() => setActiveStep((p) => Math.min(p + 1, LOADING_STEPS.length - 1)), 1800);
    } else {
      clearInterval(timerRef.current);
      clearInterval(stepRef.current);
    }
    return () => { clearInterval(timerRef.current); clearInterval(stepRef.current); };
  }, [loading]);

  const search = async (q = query) => {
    const t = (typeof q === "string" ? q : query).trim();
    if (!t) return;

    if (cache.current[t]) {
      setIsCached(true); setResult(cache.current[t]);
      setQuery(t); setError(null); return;
    }

    setIsCached(false); setLoading(true);
    setResult(null); setError(null); setQuery(t);

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": "placeholder",
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1500,
          system: SYS,
          messages: [{ role: "user", content: `請分析以下藥品：${t}` }],
        }),
      });

      const json = await res.json();
      if (!res.ok) throw new Error(json?.error?.message || `HTTP ${res.status}`);

      const text = (json.content || [])
        .filter((b) => b.type === "text")
        .map((b) => b.text)
        .join("");

      if (!text.trim()) throw new Error("回應為空，請重試");

      cache.current[t] = text;
      setResult(text);
    } catch (e) {
      setError(e.message || "查詢失敗");
    }
    setLoading(false);
  };

  const reset = () => { setResult(null); setError(null); setQuery(""); };

  const exportHTML = () => {
    if (!result) return;
    const blocks = parseResult(result);
    const body = blocks.map((b) => b.title
      ? `<div class="sec"><h3>${SECTION_ICONS[b.title]} ${b.title}</h3><pre>${b.content}</pre></div>`
      : `<pre class="raw">${b.content}</pre>`
    ).join("");
    const html = `<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><title>臨床報告 ${query}</title>
<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 24px;color:#1e293b;line-height:1.8}
h1{font-size:26px;font-weight:900;border-bottom:3px solid #4f9cf9;padding-bottom:10px;margin-bottom:8px}
.meta{font-size:12px;color:#94a3b8;margin-bottom:28px}.sec{margin-bottom:22px;padding:18px 22px;
background:#f8fafc;border-left:4px solid #4f9cf9;border-radius:0 8px 8px 0}
h3{font-size:11px;font-weight:700;color:#4f9cf9;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px}
pre{font-size:14px;color:#475569;white-space:pre-wrap;font-family:inherit;margin:0}</style>
</head><body><h1>臨床報告：${query}</h1>
<div class="meta">生成時間：${new Date().toLocaleString("zh-TW")} ｜ 僅供臨床參考</div>
${body}</body></html>`;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
    a.download = `臨床報告_${query}.html`;
    a.click();
  };

  const blocks = result ? parseResult(result) : [];

  return (
    <div style={{ minHeight: "100vh", background: "#08101f", fontFamily: "'Noto Sans TC', sans-serif", color: "#e2e8f0" }}>
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, backgroundImage: "linear-gradient(rgba(79,156,249,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(79,156,249,0.04) 1px,transparent 1px)", backgroundSize: "40px 40px" }} />

      {/* Header */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "18px 32px", borderBottom: "1px solid rgba(99,179,237,0.1)", background: "rgba(8,16,31,0.9)", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div onClick={reset} style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}>
          <div style={{ width: 36, height: 36, background: "linear-gradient(135deg,#4f9cf9,#38bdf8)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "monospace", fontWeight: 900, fontSize: 13, color: "#fff", boxShadow: "0 0 20px rgba(79,156,249,0.35)" }}>Rx</div>
          <span style={{ fontSize: 16, fontWeight: 900, letterSpacing: -0.5 }}>Clinical <span style={{ color: "#4f9cf9" }}>Pro</span></span>
        </div>
        <div style={{ fontFamily: "monospace", fontSize: 11, padding: "5px 14px", borderRadius: 99, border: `1px solid ${loading ? "rgba(79,156,249,0.4)" : isCached && result ? "rgba(16,185,129,0.3)" : "rgba(99,179,237,0.12)"}`, background: "#111827", color: loading ? "#4f9cf9" : isCached && result ? "#10b981" : "#64748b", animation: loading ? "cpulse 1.5s infinite" : "none" }}>
          {isCached && result ? "⚡ Cached" : `${timer.toFixed(1)}s`}
        </div>
      </header>

      <main style={{ maxWidth: 860, margin: "0 auto", padding: "48px 24px 100px", position: "relative", zIndex: 1 }}>

        {/* SEARCH */}
        {!result && !loading && !error && (
          <div style={{ animation: "cfadeup 0.5s ease-out" }}>
            <div style={{ textAlign: "center", marginBottom: 44 }}>
              <div style={{ display: "inline-block", fontFamily: "monospace", fontSize: 10, letterSpacing: 2, textTransform: "uppercase", color: "#4f9cf9", background: "rgba(79,156,249,0.08)", border: "1px solid rgba(79,156,249,0.2)", padding: "5px 14px", borderRadius: 99, marginBottom: 18 }}>Taiwan Clinical Pharmacy Database</div>
              <h1 style={{ fontSize: "clamp(30px,5vw,50px)", fontWeight: 900, letterSpacing: -2, lineHeight: 1.1, marginBottom: 12 }}>
                藥事快搜<br />
                <span style={{ background: "linear-gradient(135deg,#4f9cf9,#38bdf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Pro Edition</span>
              </h1>
              <p style={{ fontSize: 13, color: "#64748b", fontWeight: 300 }}>引用 TFDA 許可證 · 健保給付規範 · 臨床藥學資料庫</p>
            </div>

            <div style={{ display: "flex", background: "#111827", border: "1px solid rgba(99,179,237,0.15)", borderRadius: 16, overflow: "hidden", marginBottom: 12, boxShadow: "0 20px 60px rgba(0,0,0,0.4)" }}>
              <input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()} placeholder="輸入藥品名稱、學名或健保代碼..." autoFocus
                style={{ flex: 1, padding: "20px 24px", background: "transparent", border: "none", outline: "none", fontSize: 18, fontWeight: 700, color: "#e2e8f0", fontFamily: "'Noto Sans TC',sans-serif" }} />
              <button onClick={() => search()} disabled={!query.trim()}
                style={{ margin: 8, padding: "12px 28px", background: query.trim() ? "linear-gradient(135deg,#4f9cf9,#38bdf8)" : "#1e293b", color: query.trim() ? "#fff" : "#475569", border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: query.trim() ? "pointer" : "not-allowed", fontFamily: "'Noto Sans TC',sans-serif" }}>搜尋</button>
            </div>

            <p style={{ fontFamily: "monospace", fontSize: 11, color: "#334155", textAlign: "center", marginBottom: 24 }}>按 Enter 搜尋 · 結果自動快取至本次工作階段</p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
              {QUICK_TAGS.map((tag) => (
                <button key={tag} onClick={() => search(tag)}
                  style={{ fontFamily: "monospace", fontSize: 12, padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(99,179,237,0.15)", background: "#111827", color: "#64748b", cursor: "pointer" }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#4f9cf9"; e.currentTarget.style.borderColor = "rgba(79,156,249,0.4)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748b"; e.currentTarget.style.borderColor = "rgba(99,179,237,0.15)"; }}
                >{tag}</button>
              ))}
            </div>
          </div>
        )}

        {/* LOADING */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "80px 20px", animation: "cfadeup 0.4s ease-out" }}>
            <div style={{ position: "relative", width: 64, height: 64, marginBottom: 24 }}>
              <div style={{ width: 64, height: 64, border: "2px solid rgba(99,179,237,0.12)", borderTopColor: "#4f9cf9", borderRadius: "50%", animation: "cspin 0.8s linear infinite" }} />
              <div style={{ position: "absolute", top: "50%", left: "50%", width: 36, height: 36, border: "2px solid transparent", borderBottomColor: "#38bdf8", borderRadius: "50%", animation: "cspinr 1.2s linear infinite", transform: "translate(-50%,-50%)" }} />
            </div>
            <p style={{ fontFamily: "monospace", fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#64748b", marginBottom: 16 }}>正在查詢資料庫</p>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {LOADING_STEPS.map((step, i) => (
                <p key={i} style={{ fontFamily: "monospace", fontSize: 11, textAlign: "center", color: i <= activeStep ? "#4f9cf9" : "#334155", transition: "color 0.5s" }}>{step}</p>
              ))}
            </div>
          </div>
        )}

        {/* ERROR */}
        {error && !loading && (
          <div style={{ animation: "cfadeup 0.4s ease-out" }}>
            <button onClick={reset} style={{ background: "none", border: "none", color: "#64748b", fontWeight: 700, cursor: "pointer", fontSize: 13, marginBottom: 20, fontFamily: "'Noto Sans TC',sans-serif" }}>← 返回搜尋</button>
            <div style={{ background: "rgba(239,68,68,0.05)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 12, padding: "20px 24px", color: "#f87171", fontSize: 14, lineHeight: 1.8 }}>
              <strong>查詢失敗：</strong>{error}
            </div>
          </div>
        )}

        {/* RESULT */}
        {result && !loading && (
          <div style={{ animation: "cfadeup 0.4s ease-out" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <button onClick={reset} style={{ background: "none", border: "none", color: "#64748b", fontWeight: 700, cursor: "pointer", fontSize: 13, fontFamily: "'Noto Sans TC',sans-serif" }}>← 返回搜尋</button>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => { setResult(null); delete cache.current[query]; search(query); }}
                  style={{ fontSize: 12, fontWeight: 700, padding: "8px 18px", borderRadius: 8, border: "1px solid rgba(99,179,237,0.15)", background: "#111827", color: "#64748b", cursor: "pointer", fontFamily: "'Noto Sans TC',sans-serif" }}>重新查詢</button>
                <button onClick={exportHTML}
                  style={{ fontSize: 12, fontWeight: 700, padding: "8px 18px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#4f9cf9,#38bdf8)", color: "#fff", cursor: "pointer", fontFamily: "'Noto Sans TC',sans-serif" }}>導出報告</button>
              </div>
            </div>

            <div style={{ background: "#111827", border: "1px solid rgba(99,179,237,0.12)", borderRadius: 20, overflow: "hidden", boxShadow: "0 25px 80px rgba(0,0,0,0.5)" }}>
              <div style={{ background: "linear-gradient(135deg,#0a0f1e,#131d2e)", borderBottom: "1px solid rgba(99,179,237,0.1)", padding: "28px 36px", position: "relative", overflow: "hidden" }}>
                <div style={{ position: "absolute", right: 28, top: "50%", transform: "translateY(-50%)", fontFamily: "monospace", fontSize: 80, fontWeight: 900, color: "rgba(79,156,249,0.04)", userSelect: "none" }}>Rx</div>
                <div style={{ fontSize: "clamp(20px,3vw,28px)", fontWeight: 900, letterSpacing: -1, marginBottom: 10 }}>{query}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  {["TFDA", "NHI"].map((t) => (
                    <span key={t} style={{ fontFamily: "monospace", fontSize: 10, letterSpacing: 1.5, textTransform: "uppercase", padding: "3px 10px", borderRadius: 4, background: "rgba(79,156,249,0.1)", color: "#4f9cf9", border: "1px solid rgba(79,156,249,0.2)" }}>{t}</span>
                  ))}
                  {isCached && <span style={{ fontFamily: "monospace", fontSize: 10, padding: "3px 10px", borderRadius: 4, background: "rgba(16,185,129,0.1)", color: "#10b981", border: "1px solid rgba(16,185,129,0.2)" }}>Cached</span>}
                  <span style={{ fontFamily: "monospace", fontSize: 10, color: "#334155" }}>{new Date().toLocaleDateString("zh-TW")}</span>
                </div>
              </div>

              <div style={{ padding: "32px 36px" }}>
                {blocks.map((block, i) =>
                  block.title ? (
                    <div key={i} style={{ marginBottom: i < blocks.length - 1 ? 28 : 0, paddingBottom: i < blocks.length - 1 ? 28 : 0, borderBottom: i < blocks.length - 1 ? "1px solid rgba(99,179,237,0.08)" : "none" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "monospace", fontSize: 10, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", color: "#4f9cf9", marginBottom: 14 }}>
                        <div style={{ width: 3, height: 14, background: "#4f9cf9", borderRadius: 2, flexShrink: 0 }} />
                        {SECTION_ICONS[block.title]} {block.title}
                      </div>
                      <div style={{ fontSize: 14, lineHeight: 1.9, color: "#94a3b8", whiteSpace: "pre-wrap" }}>{block.content}</div>
                    </div>
                  ) : (
                    <div key={i} style={{ fontSize: 14, lineHeight: 1.9, color: "#94a3b8", whiteSpace: "pre-wrap" }}>{block.content}</div>
                  )
                )}
              </div>
            </div>

            <p style={{ fontFamily: "monospace", fontSize: 11, color: "#334155", textAlign: "center", marginTop: 20 }}>
              ⚠️ 本工具提供臨床參考資訊，不取代正式藥典與醫師判斷
            </p>
          </div>
        )}
      </main>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
        @keyframes cfadeup { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        @keyframes cpulse  { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes cspin   { to{transform:rotate(360deg)} }
        @keyframes cspinr  { from{transform:translate(-50%,-50%) rotate(0)} to{transform:translate(-50%,-50%) rotate(-360deg)} }
        * { box-sizing:border-box; }
        input::placeholder { color:#334155; font-weight:400; }
        ::-webkit-scrollbar { width:5px; }
        ::-webkit-scrollbar-track { background:#08101f; }
        ::-webkit-scrollbar-thumb { background:#1e293b; border-radius:99px; }
      `}</style>
    </div>
  );
}
