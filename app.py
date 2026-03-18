import streamlit as st
import google.generativeai as genai

# --- 1. 系統環境初始化 ---
APP_VERSION = "1.3.5"
SYSTEM_NAME = "慈榛驊業務管理系統（全功能終極修復版）"
st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# 配置 Gemini API (確保金鑰正確)
genai.configure(api_key="AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY")

# --- 2. 介面美化 (這就是您 HTML 檔中的設計靈魂) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F8FAFC; }}
    .block-container {{ padding-top: 1rem !important; }}
    .main-header {{ font-size: 2.5rem; font-weight: 900; color: #1E3A8A; margin-bottom: 0; }}
    .rx-tag {{ background: #2563EB; color: white; padding: 2px 10px; border-radius: 5px; font-style: italic; }}
    .report-card {{ 
        background: white; padding: 30px; border-radius: 15px; 
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #E2E8F0;
        line-height: 1.8; color: #1E293B;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯功能 ---
def run_ai_analysis(drug_name):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # 依照您的要求，採用資深醫藥主管專業口吻
        prompt = f"您是資深醫藥主管。請針對『{drug_name}』進行臨床分析：1.適應症 2.標準用法 3.禁忌。禁用粗體，分段清晰。"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"連線失敗：{str(e)}"

# --- 4. 畫面呈現 (這就是讓按鈕真正動起來的地方) ---
st.markdown(f'<h1 class="main-header"><span class="rx-tag">Rx</span> Clinical Pro</h1>', unsafe_allow_html=True)
st.caption(f"開發：慈榛驊有限公司 | 版本：{APP_VERSION}")

# 使用 Streamlit 原生輸入框，確保 Python 能抓到數值
query = st.text_input("🔍 請輸入藥品名稱 (學名或商品名)：", placeholder="例如: Holisoon, Pregabalin...", key="main_search")

if query:
    # 這裡就是解決 HTML 轉 py 無法運行的關鍵：用 status 控製執行流
    with st.status("正在檢索臨床數據...", expanded=True) as status:
        st.write("連線至雲端醫藥資料庫...")
        result_text = run_ai_analysis(query)
        st.write("分析完成。")
        status.update(label="搜尋完成！", state="complete", expanded=False)

    # 顯示結果
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📋 {query} 臨床報告")
        # 將 AI 回傳的結果塞進您設計的 HTML 卡片樣式中
        st.markdown(f'<div class="report-card">{result_text}</div>', unsafe_allow_html=True)
    
    with col2:
        st.info("💡 提醒：本報告由 AI 生成，臨床決策請依據實際仿單。")
        st.download_button(
            label="📥 下載 HTML 報告",
            data=f"<html><meta charset='UTF-8'><body>{result_text}</body></html>",
            file_name=f"{query}_report.html",
            mime="text/html"
        )

st.markdown("---")
st.caption("© 2026 慈榛驊有限公司 | 伍佰興業有限公司")
