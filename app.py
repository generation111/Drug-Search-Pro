import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="Rx Debugger", layout="wide")

# --- 1. 取得金鑰 ---
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

st.title("🛠️ API 權限診斷工具")

if not API_KEY:
    st.error("❌ Secrets 中找不到 GEMINI_API_KEY")
    st.stop()

# 顯示金鑰前 4 碼與長度 (安全檢測)
st.write(f"🔑 金鑰偵測成功：`{API_KEY[:4]}...` (長度: {len(API_KEY)})")

# --- 2. 診斷模型 ---
try:
    genai.configure(api_key=API_KEY)
    
    st.subheader("📡 掃描可用模型清單...")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            st.write(f"✅ 發現可用模型: `{m.name}`")

    if not available_models:
        st.warning("⚠️ 你的 API Key 雖然有效，但目前沒有任何模型支援 generateContent。請檢查 Google AI Studio 的專案設定。")
    else:
        # 3. 嘗試自動選取第一個能用的
        target_model = available_models[0]
        st.info(f"🚀 系統將自動嘗試使用：`{target_model}`")
        
        # 測試呼叫
        model = genai.GenerativeModel(target_model)
        response = model.generate_content("Ping", generation_config={"max_output_tokens": 5})
        st.success(f"🎊 測試成功！回應內容: {response.text}")
        
        st.balloons()
        st.markdown("---")
        st.write("請將 `app.py` 中的模型名稱改為上方顯示的 `models/...` 全名即可運作。")

except Exception as e:
    st.error(f"❌ 診斷過程發生嚴重錯誤: {e}")
    st.info("常見原因：\n1. API Key 已過期或被停用。\n2. 帳號目前的區域 (Region) 不支援此 API。")
