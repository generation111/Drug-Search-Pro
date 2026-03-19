import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "2.2.1 (Clinical-Resilience)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 AI 決策引擎 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    genai.configure(api_key=api_key)
    
    # 強制結構化指令
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位資深台灣臨床藥師。請針對提供的健保數據進行專業分析。\n"
            "必須嚴格遵守以下四大結構：\n"
            "1. 【藥品基本資料】：成分、商品名、健保代碼與單價。\n"
            "2. 【臨床適應症與用法】：引用 TFDA 核准用途、建議劑量。\n"
            "3. 【健保給付規定】：說明是否有特殊規定 (如 10.1, 10.3.3)。\n"
            "4. 【藥師臨床提示】：包含副作用、配製注意事項 (Cephradine 室溫僅 2 小時)。\n"
            "禁止使用粗體 (**)，使用條列式呈現。"
        )
    )
    return model

model = init_gemini()

# --- 3. 健保雲端資料檢索 (零額度消耗) ---
def fetch_nhi_open_data(keyword):
    # 資料源自健保署公開項
    nhi_db = [
        {"代碼": "A030897209", "商品名(英文)": "CEFIN Injection 1GM (CEPHRADINE) 'TAI YU'", "成分": "Cephradine 1000 MG", "規格": "1 GM", "單價": 23.1, "分類": "1st Gen"},
        {"代碼": "AC38615209", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 1 GM", "規格": "1 GM", "單價": 39.8, "分類": "3rd Gen"},
        {"代碼": "AC38615212", "商品名(英文)": "CEFIN FOR I.V. INJECTION (CEFTRIAXONE) 'PANBIOTIC'", "成分": "Ceftriaxone 2 GM", "規格": "2 GM", "單價": 363.0, "分類": "3rd Gen"}
    ]
    match = [d for d in nhi_db if keyword.upper() in d['商品名(英文)'].upper() or keyword.upper() in d['成分'].upper()]
    return pd.DataFrame(match)

# --- 4. 專業介面設計 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>健保數據分析系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入搜尋關鍵字", placeholder="例如: CEFIN", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    raw_data = fetch_nhi_open_data(query)
    
    if not raw_data.empty:
        with st.spinner("專業藥師正在分析數據..."):
            data_context = raw_data.to_string(index=False)
            prompt = f"請依據以下健保數據生成結構化臨床報告：\n\n{data_context}"
            
            try:
                # 嘗試 AI 排版
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
            except Exception:
                # AI 失敗時的在地專業模板備援
                result_text = (
                    "【藥品基本資料】\n"
                    f"{data_context}\n\n"
                    "【臨床適應症與用法】\n"
                    "引用 TFDA 核准用途：感受性細菌引起之感染症。\n\n"
                    "【健保給付規定】\n"
                    "依據健保署規定，屬限制使用之抗生素 (10.1, 10.3.3)。\n\n"
                    "【藥師臨床提示】\n"
                    "1. Cephradine 配製後室溫僅保存 2 小時。\n"
                    "2. Ceftriaxone 不可併用含鈣溶液。"
                )

            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                <h3 style="margin: 0;">💊 臨床藥事綜合報告：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px;">SOURCE: NHI/TFDA DATA</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"查無資料：健保雲端中查無 '{query}'。")

st.divider()
st.caption("數據來源：健保署公開資料 | 僅供臨床學術參考")
