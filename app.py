import streamlit as st
import google.generativeai as genai

# 1. 讀取金鑰 (確保您已在 Streamlit Secrets 設定 GEMINI_API_KEY)
api_key = st.secrets.get("GEMINI_API_KEY", "您的備用金鑰")
genai.configure(api_key=api_key)

# 2. 修正模型名稱為最新穩定版
try:
    # 建議使用 gemini-1.5-flash-latest 或 gemini-pro
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"模型啟動失敗: {e}")

# 3. 執行生成時的語法
# response = model.generate_content("分析藥品: Holisoon")


# API 配置 (採用您的 Gemini Key)
GEMINI_API_KEY = "AIzaSyBxhnhHvPL6zBX_vA3R6Fs7tc8tsYU8YQM"
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. 注入您的 HTML/Tailwind 視覺精髓 ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
    body, .stApp {{ font-family: 'Noto Sans TC', sans-serif; background-color: #F9FBFF; }}
    
    /* 標題與 Rx Logo 樣式 */
    .rx-logo {{
        width: 40px; height: 40px; background: #4F46E5; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 900; font-style: italic; shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4);
    }}
    .main-title {{ font-size: 2rem; font-weight: 900; color: #1E293B; margin-left: 10px; }}
    .highlight {{ color: #4F46E5; }}
    
    /* 報告卡片樣式 (對應您的 HTML 結構) */
    .report-header {{ background: #0F172A; padding: 40px; border-radius: 2.5rem 2.5rem 0 0; color: white; }}
    .report-body {{ 
        background: white; padding: 40px; border-radius: 0 0 2.5rem 2.5rem; 
        border: 1px solid #F1F5F9; line-height: 1.8; color: #334155; font-size: 1.1rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
    }}
    
    /* 讓內容頂部貼合 */
    .block-container {{ padding-top: 1.5rem !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. 分析引擎 (對應您的 React handleSearch) ---
def get_medical_analysis(drug_name):
    try:
        # 使用 Flash 模型達到您要求的「極速分析」
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # 系統指令 (System Instruction)
        sys_prompt = "你是資深臨床藥師。請極速分析藥品適應症、用法、禁忌。分段清晰，不要使用粗體語法。"
        user_prompt = f"快速臨床簡報：{drug_name}"
        
        response = model.generate_content([sys_prompt, user_prompt])
        return response.text if response else "API 未回傳資料"
    except Exception as e:
        return f"分析發生錯誤: {str(e)}"

# --- 4. 畫面呈現邏輯 ---

# 頁首 (Rx Clinical Pro)
st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 2rem;">
        <div class="rx-logo">Rx</div>
        <div class="main-title">Clinical <span class="highlight">Pro</span></div>
    </div>
""", unsafe_allow_html=True)
st.caption(f"系統版本: {臨床藥事快搜 Pro - 公開部署版} | 單位: 慈榛驊有限公司")

# 搜尋輸入 (替代 HTML 的 Form)
query = st.text_input("", placeholder="輸入藥品關鍵字 (如: Holisoon, Pregabalin)...", key="search_input")

if query:
    # 模擬您的計時器與 Loading 狀態
    start_time = time.time()
    with st.status("正在同步雲端醫學數據...", expanded=True) as status:
        st.write("連線至醫學資料庫...")
        result_text = get_medical_analysis(query)
        end_time = time.time()
        elapsed = end_time - start_time
        status.update(label=f"分析完成！耗時 {elapsed:.1f}s", state="complete", expanded=False)

    # 產出報告 (1:1 復刻您的 HTML 報告視覺)
    st.markdown("---")
    st.markdown(f"""
        <div class="report-header">
            <h2 style="font-size: 2.5rem; margin: 0;">{query}</h2>
            <p style="color: #94A3B8; font-size: 0.8rem; margin-top: 10px; font-weight: bold;">
                產出時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 版本: {CURRENT_APP_VERSION}
            </p>
        </div>
        <div class="report-body">
            {result_text.replace('\n', '<br>')}
        </div>
    """, unsafe_allow_html=True)

    # 導出與返回
    col1, col2 = st.columns([1, 4])
    with col1:
        st.download_button(
            label="📥 導出報告",
            data=f"臨床報告：{query}\n\n{result_text}",
            file_name=f"臨床報告_{query}.txt",
            mime="text/plain",
        )
    with col2:
        if st.button("↩ 返回搜尋"):
            st.rerun()

# --- 5. 頁尾 ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #94A3B8; font-size: 0.8rem;'>© 2026 {SYSTEM_NAME}</p>", unsafe_allow_html=True)
