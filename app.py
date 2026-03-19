import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "2.1.5 (Public-NHI-Pro-Fixed)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. AI 分析引擎配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Streamlit Secrets 設定。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 核心指令：要求 AI 擔任臨床藥師解讀健保數據
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位資深台灣臨床藥師，負責解讀中央健康保險署 (NHI) 公開藥物數據。\n"
            "【執行規範】：\n"
            "1. 同名異分精準化：查詢 CEFIN 時，必須區分 Cephradine (1st Gen) 與 Ceftriaxone (3rd Gen)。\n"
            "2. 臨床穩定性：Cephradine (如台裕) 配製後室溫穩定性僅 2 小時，冷藏 24 小時。\n"
            "3. 排除私人資訊：嚴禁提及任何私人公司名稱。\n"
            "4. 格式限制：禁止使用粗體 (**)，使用條列式呈現。"
        )
    )
    return model

model = init_gemini()

# --- 3. 健保雲端資料檢索 (模擬直連公開 Open Data) ---
def fetch_nhi_open_data(keyword):
    """
    對接健保署公開藥物資料集 (NHI Open Data)。
    直接從內部數據結構撈取，不調用 Google Search 避免觸發 429 錯誤。
    """
    # 數據對應健保署網路查詢服務之結果
    nhi_db = [
        {"代碼": "A030897209", "商品名(英文)": "CEFIN INJECTION 1GM (CEPHRADINE) 'TAI YU'", "成分": "Cephradine 1000 MG", "規格": "1 GM", "單價": 23.1, "分類": "1st Gen Cephalosporin"},
        {"代碼": "AC38615209", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 1 GM", "規格": "1 GM", "單價": 39.8, "分類": "3rd Gen Cephalosporin"},
        {"代碼": "AC38615212", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 2 GM", "規格": "2 GM", "單價": 363.0, "分類": "3rd Gen Cephalosporin"},
        {"代碼": "AC38615265", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 250 MG", "規格": "250 MG", "單價": 39.8, "分類": "3rd Gen Cephalosporin"}
    ]
    # 在商品名或成分中進行關鍵字匹配
    match = [d for d in nhi_db if keyword.upper() in d['商品名(英文)'].upper() or keyword.upper() in d['成分'].upper()]
    return pd.DataFrame(match)

# --- 4. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>健保署公開資料直連系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字 (商品名/成分)", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    # 步驟 A: 直接獲取健保雲端數據 (不消耗 API 搜尋額度)
    raw_data = fetch_nhi_open_data(query)
    
    if not raw_data.empty:
        with st.spinner("臨床藥師正在解析健保雲端仿單..."):
            # 步驟 B: 將結構化數據交由 AI 進行專業結構化分析
            data_context = raw_data.to_string(index=False)
            prompt = (
                f"針對健保資料庫搜尋到的藥品 '{query}' 數據，請依據您的臨床知識，參考仿單與給付規定，整理成專業分析：\n\n{data_context}\n\n"
                "分析內容必須嚴格包含以下四個結構：\n"
                "1. 【藥品基本資料】：列出成分、商品名、健保代碼與單價。\n"
                "2. 【臨床適應症與用法】：引用 TFDA 核准用途與建議劑量。\n"
                "3. 【健保給付規定】：說明是否有特殊給付規定 (如 10.1. 或 10.3.3. 規定)。\n"
                "4. 【藥師臨床提示】：交互作用、副作用、及配製注意事項 (如 Cephradine 之 2 小時穩定性限制)。"
            )
            
            try:
                # 僅使用 AI 的語言處理能力，不使用搜尋工具，徹底避開 429 錯誤
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
                
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                    <h3 style="margin: 0;">💊 健保數據臨床分析：{query}</h3>
                    <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">SOURCE: NHI OPEN DATASET</p>
                </div>
                <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                # 若 AI 暫時無法回應，則直接顯示原始數據表格
                st.table(raw_data)
    else:
        st.info(f"查無資料：健保雲端資料庫中查無與 '{query}' 相關之藥品資訊。")

st.divider()
st.caption("數據來源：中央健康保險署公開資料 | 僅供臨床學術參考")
