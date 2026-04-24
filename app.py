# app.py
import streamlit as st
import sana_config as cfg
import sana_engine as engine
import re

# ==========================================
# 1. 頁面與狀態初始化
# ==========================================
st.set_page_config(page_title="Sana VFO 認知終端", layout="wide", initial_sidebar_state="expanded")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "scene_setting" not in st.session_state:
    st.session_state.scene_setting = "我們現在正在進行一場普通的初次見面談話。"

# ==========================================
# 2. 側邊欄：API、模型鎖定與場景切換
# ==========================================
with st.sidebar:
    st.title("⚙️ Sana VFO 系統控制")
    api_key = st.text_input("🔑 API 金鑰", value=cfg.DEFAULT_API_KEY, type="password")
    
    if api_key:
        if st.button("🔄 重新整理可用模型清單") or not st.session_state.available_models:
            with st.spinner("正在向 Google 請求可用模型..."):
                try:
                    st.session_state.available_models = engine.fetch_available_models(api_key)
                except Exception as e:
                    st.error(f"無法獲取清單: {e}")

        if st.session_state.available_models:
            default_idx = 0
            for i, m in enumerate(st.session_state.available_models):
                if "pro-preview" in m or "3.1-pro" in m:
                    default_idx = i
                    break
                elif "1.5-pro" in m:
                    default_idx = i
            
            selected_model = st.selectbox("🤖 選擇運算核心 (Model)", st.session_state.available_models, index=default_idx)
            st.info(f"當前模型：{selected_model}")
        else:
            st.error("未發現可用模型，請檢查金鑰。")
            
    st.markdown("---")
    
    # 【新增功能】動態場景前提注入
    st.markdown("### 🎬 互動場景前提")
    st.caption("在此隨時改變故事背景，AI 會在『下一回合』自動套用新設定。")
    new_scene = st.text_area("當前場景設定", value=st.session_state.scene_setting, height=80)
    if new_scene != st.session_state.scene_setting:
        st.session_state.scene_setting = new_scene
        
    st.markdown("---")
    st.markdown("### 📦 模組說明速查")
    category = st.selectbox("選擇模組分類", list(cfg.MODULES_FOR_UI.keys()))
    for mod_name, mod_desc in cfg.MODULES_FOR_UI[category].items():
        with st.expander(f"🔹 {mod_name}"):
            st.caption(mod_desc)

# ==========================================
# 3. 雙欄式主畫面：左側對話區 / 右側即時分析板
# ==========================================
col_chat, col_dash = st.columns([7, 3], gap="large")

with col_chat:
    st.title("Sana 核心認知終端")
    
    # 渲染歷史對話 (100% 乾淨)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("輸入對話..."):
        if not api_key:
            st.error("請先配置 API Key。")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(f'Sana ({selected_model}) VFO v7.3 運算中...'):
                try:
                    # 修復記憶斷層：強迫 AI 看見自己上一輪完整的 VFO 英文推演
                    history_for_api = []
                    for m in st.session_state.messages[:-1]:
                        if m["role"] == "user":
                            history_for_api.append({"role": "user", "parts": [m["content"]]})
                        else:
                            full_memory = m.get("raw_text", m["content"])
                            history_for_api.append({"role": "model", "parts": [full_memory]})
                            
                    forced_input = cfg.get_forced_template(user_input)
                    
                    # 動態組合 System Prompt：將玩家輸入的場景作為最高層級指令覆寫
                    dynamic_system_prompt = cfg.SYSTEM_PROMPT + f"\n\n【System Absolute Override - 當前互動場景與前提】：\n{st.session_state.scene_setting}"
                    
                    result = engine.process_sana_turn(
                        api_key=api_key,
                        selected_model=selected_model,
                        system_prompt=dynamic_system_prompt,
                        history_for_api=history_for_api,
                        forced_template_text=forced_input
                    )
                    
                    st.markdown(result["output"])
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "raw_text": result["raw_full_text"],     
                        "content": result["output"],
                        "parsed_dash": result["parsed_dash"]
                    })
                    st.rerun() 

                except Exception as e:
                    st.error(f"運算中斷：{str(e)}")

# ==========================================
# 4. 右側欄：Sana 實時狀態監測板 (全中文 UI)
# ==========================================
with col_dash:
    st.subheader("📊 Sana VFO 監測板")
    st.markdown("*(擷取自最新一輪神經運算)*")
    st.divider()
    
    latest_msg = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant":
            latest_msg = msg
            break
            
    if latest_msg and latest_msg.get("parsed_dash"):
        d = latest_msg["parsed_dash"]
        
        # 面具疲勞度警告條
        mf_val = d.get('mf', '20').split('(')[0].strip()
        st.markdown(f"**🎭 面具疲勞度 (MF): {mf_val} / 100**")
        try:
            # 防呆：確保 mf_val 裡面沒有夾雜其他文字
            clean_mf = int(float(re.search(r'\d+', mf_val).group()))
            st.progress(min(clean_mf, 100))
        except:
            pass
        
        st.markdown("**🛡️ 模組 9: 圖靈測試防禦機制**")
        if d.get("ai_scan", "0") != "0" and d.get("ai_scan") != "No Data":
            st.error(f"⚠️ 偵測到 AI 塑膠味！入侵值: {d.get('ai_scan')}")
        else:
            st.success("安全 (未觸發物理打斷)")
            
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("L (好感度)", d.get("l_val", "0").split('(')[0].strip())
            st.metric("SAI (主導權/地位)", d.get("sai", "50").split('(')[0].strip())
        with col2:
            st.metric("T (信任度)", d.get("t_val", "0").split('(')[0].strip())
            st.metric("B-D (邊界防禦)", d.get("bd", "100").split('(')[0].strip())
            
        st.markdown("**🧠 模組 B: 戰略判斷 (Introspection)**")
        st.info(d.get("mod_b", "無資料"))
        
        st.markdown("**🌋 模組 C: 真實內在反射 (True Inner Reflex)**")
        st.warning(d.get("mod_c", "無資料"))
        
        st.markdown("**🎭 模組 D: 職業面具偽裝 (Professional Mask)**")
        st.success(d.get("mod_d", "無資料"))
        
        st.markdown("**🎯 模組 A: 次輪準備 (Next Round Prep)**")
        st.write(d.get("mod_a", "無資料"))
        
        # 🔥 將 Raw Log 流放到最角落
        st.divider()
        st.caption("⚙️ 開發者底層監控")
        with st.expander("🔍 展開 VFO 原始推演 Log (Raw Data)", expanded=False):
            st.code(latest_msg.get("raw_text", "無資料"), language="markdown")
        
    else:
        st.caption("等待首輪對話產生 VFO 數據...")
