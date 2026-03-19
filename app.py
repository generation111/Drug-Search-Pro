import streamlit as st
import google.generativeai as genai

# --- 1. 系統配置 ---
CURRENT_APP_VERSION = "1.8.0 (Hybrid-Engine)"
st.set_page_config(page_title="Rx Clinical Pro", layout="wide", page_icon="💊")

# --- 2. 核心 API 配置 ---
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 宣告工具：僅在必要時調用
    tools = [{"google_search_retrieval": {}}]

    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        tools=tools,
        system_instruction=(
            "你是一位資深台灣臨床藥師。你的任務是精準分析藥品。\n"
            "【處理優先級】：\n"
            "1. 內建核心藥品 (零額度消耗)：\n"
            "   - 若查詢 CEFIN，必須區分：\n"
            "     * Cephradine (台裕希芬黴素)：A030897209, 23.1元。配製後室溫僅2小時。\n"
            "     * Ceftriaxone (舒復)：AC38615系列，第三代頭孢菌素。\n"
            "2. 其他藥品 (聯網檢索)：\n"
            "   - 若非上述藥品，請啟動 google_search 檢索 TFDA 仿單。\n"
            "   - 禁止模糊推論 (如 Cefazolin)。查不到請報查無。\n"
            "3. 格式：禁止使用粗體 (**)，條列式呈現。"
        )
    )
    return model

model = init_gemini()

# --- 3. 介面與邏輯 ---
st.markdown("<h1 style='text-align: center; margin-top: -60px;'>Rx Clinical <span style='color: #4F46E5;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #64748b;'>混合動力檢索系統 | V{CURRENT_APP_VERSION}</p>", unsafe_allow_html=True)

query = st.text_input("輸入藥品關鍵字", placeholder="例如: CEFIN 或 HOLISOON", label_visibility="collapsed")

if query:
    query = query.strip().upper()
    
    with st.spinner(f"正在分析 '{query}' 的臨床數據..."):
        try:
            # 判斷是否為核心藥品以決定是否強制聯網
            is_core_drug = any(name in query for name in ["CEFIN", "希芬", "舒復"])
            
            if is_core_drug:
                # 核心藥品：直接由 System Instruction 輸出，不調用工具以節省額度
                prompt = f"請提供內建藥品 '{query}' 的詳細臨床分析對照表。"
                response = model.generate_content(prompt)
            else:
                # 非核心藥品：正常調用聯網工具
                prompt = f"請檢索並分析台灣健保藥品 '{query}' 的成分、代碼與適應症。若不確定請回答查無資訊。"
                response = model.generate_content(prompt)
            
            result_text = response.text.replace('**', '')

            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 25px; border-radius: 15px 15px 0 0; color: white;">
                <h3 style="margin: 0;">💊 臨床藥事分析：{query}</h3>
                <p style="font-size: 11px; color: #94a3b8; margin-top: 5px; letter-spacing: 1px;">{"CORE DATA MODE" if is_core_drug else "LIVE SEARCH MODE"}</p>
            </div>
            <div style="background-color: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 15px 15px; color: #334155; line-height: 1.8; white-space: pre-wrap;">
{result_text}
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ 外部檢索流量已滿，暫時無法查詢新藥品。核心藥品 (如 CEFIN) 仍可查詢。")
            else:
                st.error(f"系統診斷錯誤：{e}")

st.divider()
st.caption("數據來源：TFDA & 健保署 | 核心知識庫已手動校準")
