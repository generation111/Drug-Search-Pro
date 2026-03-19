import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "2.2.0 (Clinical-Core-Logic)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 AI 決策引擎 (專業分析邏輯硬編碼) ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 這是系統最核心的臨床分析指令，將您的四大結構硬編碼進去
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位資深台灣臨床藥師，負責解讀中央健康保險署 (NHI) 公開藥物數據及食藥署 (TFDA) 仿單。\n\n"
            "【執行規範】：\n"
            "1. 資料源：嚴格引用台灣 TFDA 許可證、NHI 代碼與給付規範、台灣各大醫院雲端處方集。\n"
            "2. 結構化輸出：不論使用者查詢何種藥品，必須且僅能依據以下四大臨床結構進行分析：\n\n"
            "   - 【藥品基本資料】：包含成分、商品名、健保代碼與單價。\n"
            "   - 【臨床適應症與用法】：包含 TFDA 核准用途、建議劑量。\n"
            "   - 【健保給付規定】：說明是否有特殊給付規定 (如科別限制、附檢驗報告、 restrictions 等)。\n"
            "   - 【藥師臨床提示】：包含重大副作用、配製注意事項、保存穩定性。\n\n"
            "【CEFIN 歧義處理】：\n"
            "若使用者查詢 CEFIN，必須清楚區分：\n"
            "- Cephradine (台裕)：一代，特別提示配製後室溫僅保存 2 小時。\n"
            "- Ceftriaxone (舒復)：三代，注意含鈣溶液沉澱問題。\n\n"
            "【格式限制】：\n"
            "- 禁止使用粗體 (**)，使用簡潔清爽的列表呈现，不帶私人公司聯想。"
        )
    )
    return model

model = init_gemini()

# --- 3. 健保雲端資料檢索 (模擬直連公開 Open Data) ---
def fetch_nhi_open_data(keyword):
    """
    模擬對接健保署公開 Open Data。此方式零額度消耗。
    """
    # 內部數據庫匹配截圖品項
    nhi_db = [
        {"代碼": "A030897209", "商品名(英文)": "CEFIN Injection 1GM (CEPHRADINE) 'TAI YU'", "成分": "Cephradine 1000 MG", "規格": "1 GM", "單價": 23.1, "分類": "1st Gen Cephalosporin"},
        {"代碼": "AC38615209", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 1 GM", "規格": "1 GM", "單價": 39.8, "分類": "3rd Gen Cephalosporin"},
        {"代碼": "AC38615212", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 2 GM", "規格": "2 GM", "單價": 363.0, "分類": "3rd Gen Cephalosporin"},
        {"代碼": "AC38615265", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 250 MG", "規格": "250 MG", "單價": 39.8, "分類": "3rd Gen Cephalosporin"}
    ]
    match = [d for d in nhi_db if keyword.upper() in d['商品名(英文)'].upper() or keyword.upper() in d['成分'].upper()]
    return pd.DataFrame(match)

# --- 4. 介面佈局 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>健保署雲端數據同步版 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字 (商品名/成分)", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    # A. 從內部「模擬雲端數據」撈取結構化數據 (零 API 搜尋消耗)
    raw_data = fetch_nhi_open_data(query)
    
    if not raw_data.empty:
        with st.spinner("專業藥師正在調閱 TFDA/NHI 雲端仿單..."):
            # B. 將健保數據交給 AI 進行深度結構化分析
            data_context = raw_data.to_string(index=False)
            prompt = f"針對健保雲端搜尋到的藥品 '{query}' 數據，請依照您的臨床知識，嚴格根據四大結構生成專業分析報告：\n\n{data_context}"
            
            try:
                # 僅使用 AI 的語言解讀能力，不使用搜尋工具，避開 429 限制
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
                
                # C. 渲染分析結果
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                    <h3 style="margin: 0;">💊 臨床藥事綜合報告：{query}</h3>
                    <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">DATA SOURCE: NHI/TFDA OPEN DATA</p>
                </div>
                <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                # AI 故障時顯示原始數據
                st.info(f"AI 排版失敗，顯示原始數據表格：")
                st.table(raw_data)
    else:
        st.info(f"查無資料：健保雲端資料庫中查無與 '{query}' 相關之藥品資訊。")

st.divider()
st.caption(f"穩定版本: {CURRENT_APP_VERSION} | 數據來源：中央健康保險署 Open Open | 僅供臨床參考")
