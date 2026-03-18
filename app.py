import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- 1. 系統配置 (確保標題貼近頂部) ---
APP_VERSION = "1.3.5"
SYSTEM_NAME = "慈榛驊業務管理系統（全功能終極修復版）"
st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# API 配置 (採用您目前的 Key)
GEMINI_API_KEY = "AIzaSyBNCEYq92cGpGYgoSgV9RrHHMwKYt4tHScY"
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. 介面美化控製 (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .block-container { padding-top: 1rem !important; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #1E3A8A; margin-bottom: 0.5rem; }
    .report-box { 
        background: white; padding: 25px; border-radius: 12px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;
        white-space: pre-wrap; line-height: 1.8;
    }
    h2 { color: #2563EB; border-left: 5px solid #2563EB; padding-left: 12px; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 分析引擎 (優化超時處理) ---
def get_medical_report(drug_name):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # 依照您的要求，採用資深醫藥主管推廣口吻
        prompt = (
            f"您是一位資深醫藥推廣主管。請針對藥品『{drug_name}』產出專業臨床摘要。\n\n"
            f"結構要求：\n"
            f"## 1. 主要適應症\n"
            f"## 2. 臨床建議用法\n"
            f"## 3. 安全性注意事項\n\n"
            f"規範：使用繁體中文，分段清晰，不使用粗體(**)，若有商品名請加註英文名。"
        )
        response = model.generate_content(prompt)
        return response.text if response else "無法取得分析內容。"
    except Exception as e:
        return f"系統連線異常: {str(e)}"

# --- 4. 畫面佈局 ---
st.markdown(f'<div class="main-header">🧬 {SYSTEM_NAME}</div>', unsafe_allow_html=True)
st.caption(f"開發單位：慈榛驊有限公司 | 當前版本：{APP_VERSION}")

# 藥品搜尋輸入區
query = st.text_input("🔍 藥品臨床數據查詢：", placeholder="輸入學名或商品名 (如: Holisoon, Pregabalin)...")

if query:
    # 使用 st.empty() 建立動態更新區塊，避免畫面卡死
    report_area = st.empty()
    
    with st.spinner(f"正在分析 {query} 的臨床數據，請稍候..."):
        # 執行分析
        result = get_medical_report(query)
        
        # 渲染結果
        with report_area.container():
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### 📋 {query} 臨床報告摘要")
                st.markdown(f'<div class="report-box">{result}</div>', unsafe_allow_html=True)
            with col2:
                st.info("💡 **專業建議**：\n此分析由 AI 生成，臨床應用請務必查閱官方仿單。")
                
                # 檔案導出功能
                st.download_button(
                    label="📥 下載 HTML 報告",
                    data=f"<h3>{query} 臨床摘要</h3><hr>{result}",
                    file_name=f"{query}_Report.html",
                    mime="text/html",
                    use_container_width=True
                )

# --- 5. 頁尾 ---
st.markdown("---")
st.caption("© 2026 慈榛驊有限公司 | 伍佰興業有限公司 聯合開發")
