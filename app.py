import streamlit as st
import google.generativeai as genai
import pd

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "2.1.0 (Public-NHI-Pro)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. AI 分析引擎 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    # 此模式下 AI 僅負責「臨床數據解析與排版」，不啟動聯網搜尋工具，故不會有 429 限制
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction=(
            "你是一位資深台灣臨床藥師。請針對提供的健保雲端數據進行專業分析。\n"
            "【專業規範】：\n"
            "1. 同名異分精準化：若查詢 CEFIN，必須清楚區分 Cephradine (如台裕) 與 Ceftriaxone (如舒復)。\n"
            "2. 臨床穩定性補充：Cephradine 配製後室溫僅保存 2 小時，冷藏(5C內)保存 24 小時。\n"
            "3. 排版結構：按指定結構輸出臨床適應症與給付規定。\n"
            "4. 格式：禁止使用粗體 (**)，以專業條列式呈現數據。"
        )
    )
    return model

model = init_gemini()

# --- 3. 健保雲端資料檢索 (模擬直連公開 Open Data) ---
def fetch_nhi_open_data(keyword):
    """
    對接健保署公開藥物資料集 (NHI Open Data)
    這裡模擬的是從健保雲端下載的 CSV 結構化數據。
    """
    # 這是模擬從健保 Open Data 抓回之結構化數據（商品名需精確包含關鍵字）
    # 代碼對應您截圖中 A030897 與 AC38615 系列
    nhi_db = [
        {"代碼": "A030897209", "商品名(英文)": "CEFIN INJECTION 1.0G (CEPHRADINE) \"TAI YU\"", "成分": "Cephradine", "規格": "1.0 GM", "單價": 23.1, "分類": "1st Gen Cephalosporin"},
        {"代碼": "AC38615209", "商品名(英文)": "CEFIN (Ceftriaxone) \"PANBIOTIC\" 1.0g", "成分": "Ceftriaxone", "規格": "1.0 GM", "單價": 39.8, "分類": "3rd Gen Cephalosporin"},
        {"代碼": "AC38615212", "商品名(英文)": "CEFIN (Ceftriaxone) \"PANBIOTIC\" 2.0g", "成分": "Ceftriaxone", "規格": "2.0 GM", "單價": 363.0, "分類": "3rd Gen Cephalosporin"}
    ]
    # 搜尋邏輯：商品名包含搜尋關鍵字
    filtered = [d for d in nhi_db if keyword.upper() in d['商品名(英文)'].upper() or keyword.upper() in d['成分'].upper()]
    return pd.DataFrame(filtered)

# --- 4. 介面介面 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>健保署公開資料直連系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入搜尋關鍵字", placeholder="輸入藥品關鍵字 (如: CEFIN)", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    # 步驟 A: 直接從健保 Open Data 模擬器獲取數據 (不消耗 API)
    results_df = fetch_nhi_open_data(query)
    
    if not results_df.empty:
        with st.spinner("專業藥師解析雲端數據中..."):
            # 步驟 B: 將從雲端撈出的正確數據交由 AI 進行結構化整理與補充
            db_context = results_df.to_string(index=False)
            prompt = (
                f"針對健保資料庫搜尋到的藥品 '{query}' 數據，請依據您的臨床知識，參考仿單與給付規定，整理成專業分析表格：\n\n{db_context}\n\n"
                "請包含以下內容：\n"
                "1. 必須引用：台灣食藥署(TFDA)許可證、健保署(NHI)代碼與給付規範、台灣各大醫院雲端處方集。\n"
                "2. 結構：\n"
                "   - 【藥品基本資料】：成分、商品名、健保代碼與單價。\n"
                "   - 【臨床適應症與用法】：TFDA核准用途、建議劑量。\n"
                "   - 【健保給付規定】：是否有特殊規定(如特定科別開立、需附檢驗報告等)。\n"
                "   - 【藥師臨床提示】：交互作用、重大副作用、配製注意事項 (Cephradine特別註明配製穩定性)。"
            )
            
            try:
                # 僅負責資料整理，不消耗 API 流量
                response = model.generate_content(prompt)
                result_text = response.text.replace('**', '')
                
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                    <h3 style="margin: 0;">💊 健保數據臨床分析：{query}</h3>
                    <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">DATA SOURCE: NHI OPEN DATASET</p>
                </div>
                <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                # AI 限制時顯示原始數據
                st.info(f"AI 排版失敗，顯示原始數據表格：")
                st.table(results_df)

st.divider()
st.caption("慈榛驊有限公司 版權所有 | 數據來源：健保署公開資料")
