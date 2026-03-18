import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime

# --- 系統配置 ---
# 根據您的需求，標題需貼近頁面上緣
APP_VERSION = "1.3.5"
ST_TITLE = "臨床藥事快搜 Pro"
st.set_page_config(page_title=ST_TITLE, layout="wide")

# API 配置 (加入 .strip() 避免不可見字元導致 Illegal header 錯誤)
GEMINI_API_KEY = "AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY".strip()
genai.configure(api_key=GEMINI_API_KEY)

# --- 介面美化 ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    /* 讓系統標題盡量貼近頁面上緣 */
    .block-container { padding-top: 1.5rem !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #1E3A8A; margin-bottom: 0; }
    .rx-tag { background: #2563EB; color: white; padding: 2px 10px; border-radius: 5px; font-style: italic; }
    .report-container { 
        background: white; 
        padding: 25px; 
        border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        border: 1px solid #E2E8F0;
        line-height: 1.6;
        color: #1E293B;
    }
    h2 { color: #2563EB; border-left: 5px solid #2563EB; padding-left: 10px; margin-top: 20px; font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

# --- 功能邏輯 ---
def fetch_med_info(drug_name):
    """
    呼叫 Gemini AI 進行專業藥事分析
    採用資深醫藥主管與藥師語氣
    """
    try:
        # 使用 Flash 模型以維持極速反應
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # 提示詞優化：加入專業藥師語氣與排版規範
        prompt = (
            f"您現在是一位具備資深醫藥主管背景的藥師。"
            f"請針對藥品『{drug_name}』進行專業且精簡的臨床分析。"
            f"內容必須包含：\n"
            f"1. 適應症 (Indications)\n"
            f"2. 標準用法 (Dosage & Administration)\n"
            f"3. 關鍵禁忌與警告 (Contraindications & Warnings)\n\n"
            f"格式規範：\n"
            f"- 使用 ## 作為中標題\n"
            f"- 內容請分段清晰\n"
            f"- 禁用粗體語法 (**)\n"
            f"- 若提及商品名，請註記其英文名 (如 Holisoon)"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 檢索中斷：{str(e)}\n\n請確認您的網路連線或 API 金鑰是否有效。"

# --- UI 佈局 ---
# 標題與版本資訊
st.markdown(f'<h1 class="main-header"><span class="rx-tag">Rx</span> Clinical Pro</h1>', unsafe_allow_html=True)
st.caption(f"專業藥事情報系統 | 版本代號：{APP_VERSION}")

# 搜尋輸入框
query = st.text_input("🔍 請輸入藥品名稱 (學名或商品名)：", placeholder="例如: Holisoon, Pregabalin...", key="search_input")

if query:
    # 狀態顯示器
    with st.status("正在檢索臨床數據...", expanded=True) as status:
        st.write("連線至醫學資料庫並進行 AI 分析...")
        result_text = fetch_med_info(query)
        st.write("分析完成。")
        status.update(label="檢索成功！", state="complete", expanded=False)
    
    # 顯示結果區域
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📋 {query} 臨床摘要報告")
        # 封裝在白色容器中以提升視覺質感
        st.markdown(f'<div class="report-container">{result_text}</div>', unsafe_allow_html=True)
    
    with col2:
        st.info("💡 **臨床決策提醒**\n本報告由 AI 生成，僅供醫療專業人員參考。具體劑量與禁忌請務必查閱官方最新仿單資料。")
        
        # 檔案下載功能
        timestamp = datetime.now().strftime("%Y%m%d")
        st.download_button(
            label="📥 下載 PDF/HTML 格式",
            data=f"<h2>{query} 臨床報告</h2><hr>{result_text}",
            file_name=f"{query}_Report_{timestamp}.html",
            mime="text/html",
            use_container_width=True
        )

# --- 底部宣告 ---
st.markdown("---")
st.caption("© 2026 慈榛驊有限公司 | 臨床數據由 Google Gemini 提供")
