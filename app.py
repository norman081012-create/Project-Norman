# app.py
import streamlit as st
import avatar_config as cfg
import avatar_engine as engine
import re

# ==========================================
# 1. 狀態與路由初始化
# ==========================================
st.set_page_config(page_title="Project AVATAR 認知終端", layout="wide", initial_sidebar_state="expanded")

if "current_page" not in st.session_state:
    st.session_state.current_page = "manager"

# 人物資料庫：{ "角色名稱": { "age":.., "gender":.., "matrix": "...", "messages": [], "scene": "..." } }
if "avatars" not in st.session_state:
    st.session_state.avatars = {}
if "active_avatar_name" not in st.session_state:
    st.session_state.active_avatar_name = None
if "available_models" not in st.session_state:
    st.session_state.available_models = []

# ==========================================
# 2. 側邊欄：全局設定
# ==========================================
with st.sidebar:
    st.title("⚙️ AVATAR 系統控制")
    api_key = st.text_input("🔑 API 金鑰", value=cfg.DEFAULT_API_KEY, type="password")
    
    selected_model = None
    if api_key:
        if st.button("🔄 獲取模型清單") or not st.session_state.available_models:
            with st.spinner("請求中..."):
                try:
                    st.session_state.available_models = engine.fetch_available_models(api_key)
                except Exception as e:
                    st.error(f"錯誤: {e}")

        if st.session_state.available_models:
            default_idx = next((i for i, m in enumerate(st.session_state.available_models) if "pro-preview" in m or "3.1-pro" in m), 0)
            selected_model = st.selectbox("🤖 運算核心", st.session_state.available_models, index=default_idx)

# ==========================================
# 3. 頁面 1：人物建檔與管理庫 (Manager Page)
# ==========================================
def render_manager_page():
    st.title("🌌 Project AVATAR - 人格容器庫")
    st.markdown("在此建立新的意識容器，或選擇已建立的人格進行深度模擬。")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("➕ 建立新容器 (New Avatar)")
        with st.form("new_avatar_form"):
            a_name = st.text_input("人物代號 (Name)*", placeholder="例如：Alex")
            col_a, col_g = st.columns(2)
            with col_a:
                a_age = st.number_input("年齡", min_value=1, max_value=120, value=33)
            with col_g:
                a_gender = st.selectbox("性別", ["男性", "女性", "非二元", "保密"])
            
            a_seeds = st.text_area("自定義種子 (用逗號或換行分隔)", placeholder="例如：個性機車, 很有主見, 喜歡寫程式")
            
            submit_btn = st.form_submit_button("🚀 注入靈魂並生成矩陣", type="primary")
            
            if submit_btn:
                if not api_key or not selected_model:
                    st.error("請先在側邊欄設定 API Key 與模型。")
                elif not a_name:
                    st.error("請填寫人物代號！")
                elif a_name in st.session_state.avatars:
                    st.error("此代號已存在，請換一個名字。")
                else:
                    first_seed = f"{a_age}歲{a_gender}"
                    other_seeds = [s.strip() for s in a_seeds.replace('\n', ',').split(',') if s.strip()]
                    all_seeds = [first_seed] + other_seeds
                    
                    with st.spinner("正在編譯核心模塊矩陣 (這可能需要幾十秒)..."):
                        try:
                            generated_matrix = engine.generate_avatar_matrix(api_key, selected_model, all_seeds)
                            st.session_state.avatars[a_name] = {
                                "name": a_name,
                                "first_seed": first_seed,
                                "seeds": other_seeds,
                                "matrix": generated_matrix,
                                "messages": [], 
                                "scene": "我們現在正在進行一場普通的初次見面談話。"
                            }
                            st.success(f"✅ {a_name} 意識容器建立完成！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"矩陣生成失敗: {str(e)}")

    with col2:
        st.subheader("📂 已存檔容器 (Active Avatars)")
        if not st.session_state.avatars:
            st.info("目前沒有任何人物檔案。請在左側建立。")
        else:
            for name, data in st.session_state.avatars.items():
                with st.expander(f"👤 {name} ({data['first_seed']})", expanded=True):
                    st.caption(f"附加種子: {', '.join(data['seeds']) if data['seeds'] else '無'}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"▶️ 進入 {name} 模擬", key=f"sim_{name}"):
                            st.session_state.active_avatar_name = name
                            st.session_state.current_page = "simulation"
                            st.rerun()
                    with col_btn2:
                        with st.popover("🔍 查看靈魂矩陣"):
                            st.code(data['matrix'], language="markdown")

# ==========================================
# 4. 頁面 2：核心認知終端 (Simulation Page)
# ==========================================
def render_simulation_page():
    avatar_name = st.session_state.active_avatar_name
    avatar_data = st.session_state.avatars[avatar_name]
    
    col_nav1, col_nav2 = st.columns([1, 9])
    with col_nav1:
        if st.button("⬅️ 返回人物庫"):
            st.session_state.current_page = "manager"
            st.rerun()
    with col_nav2:
        st.markdown(f"### 🧠 測試對象：**{avatar_name}** | 核心種子：{avatar_data['first_seed']}")
    
    st.divider()

    new_scene = st.text_input("🎬 當前互動場景前提", value=avatar_data['scene'])
    if new_scene != avatar_data['scene']:
        st.session_state.avatars[avatar_name]['scene'] = new_scene

    col_chat, col_dash = st.columns([7, 3], gap="large")

    with col_chat:
        for msg in avatar_data['messages']:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_input := st.chat_input(f"對 {avatar_name} 說點什麼..."):
            if not api_key:
                st.error("請先配置 API Key。")
                st.stop()
            
            st.session_state.avatars[avatar_name]["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner(f'{avatar_name} 運算中...'):
                    try:
                        history_for_api = []
                        for m in avatar_data["messages"][:-1]:
                            if m["role"] == "user":
                                history_for_api.append({"role": "user", "parts": [m["content"]]})
                            else:
                                full_memory = m.get("raw_text", m["content"])
                                history_for_api.append({"role": "model", "parts": [full_memory]})
                                
                        forced_input = cfg.get_forced_template(user_input)
                        
                        # 動態拼接：專屬矩陣 + 底層規則 + 場景
                        dynamic_system_prompt = (
                            avatar_data['matrix'] + "\n\n" + 
                            cfg.BASE_SYSTEM_RULES + 
                            f"\n\n【System Absolute Override - 當前互動場景與前提】：\n{avatar_data['scene']}"
                        )
                        
                        result = engine.process_avatar_turn(
                            api_key=api_key,
                            selected_model=selected_model,
                            system_prompt=dynamic_system_prompt,
                            history_for_api=history_for_api,
                            forced_template_text=forced_input
                        )
                        
                        st.markdown(result["output"])
                        
                        st.session_state.avatars[avatar_name]["messages"].append({
                            "role": "assistant",
                            "raw_text": result["raw_full_text"],     
                            "content": result["output"],
                            "parsed_dash": result["parsed_dash"]
                        })
                        st.rerun() 

                    except Exception as e:
                        st.error(f"運算中斷：{str(e)}")

    with col_dash:
        st.subheader(f"📊 {avatar_name} VFO 監測板")
        st.markdown("*(擷取自最新一輪神經運算)*")
        st.divider()
        
        latest_msg = None
        for msg in reversed(avatar_data["messages"]):
            if msg["role"] == "assistant":
                latest_msg = msg
                break
                
        if latest_msg and latest_msg.get("parsed_dash"):
            d = latest_msg["parsed_dash"]
            
            mf_val = d.get('mf', '20').split('(')[0].strip()
            st.markdown(f"**🎭 面具疲勞度 (MF): {mf_val} / 100**")
            try:
                clean_mf = int(float(re.search(r'\d+', mf_val).group()))
                st.progress(min(clean_mf, 100))
            except:
                pass
            
            st.markdown("**🛡️ 圖靈測試防禦機制**")
            if d.get("ai_scan", "0") != "0" and d.get("ai_scan") != "No Data":
                st.error(f"⚠️ 偵測到 AI 塑膠味！入侵值: {d.get('ai_scan')}")
            else:
                st.success("安全 (未觸發物理打斷)")
                
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("L (好感度)", d.get("l_val", "0").split('(')[0].strip())
                st.metric("SAI (地位感知)", d.get("sai", "50").split('(')[0].strip())
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
            
            st.divider()
            st.caption("⚙️ 開發者底層監控")
            with st.expander("🔍 展開 VFO 原始推演 Log (Raw Data)", expanded=False):
                st.code(latest_msg.get("raw_text", "無資料"), language="markdown")
        else:
            st.caption("等待首輪對話產生 VFO 數據...")

# ==========================================
# 5. 主程式路由執行
# ==========================================
if st.session_state.current_page == "manager":
    render_manager_page()
elif st.session_state.current_page == "simulation":
    if st.session_state.active_avatar_name:
        render_simulation_page()
    else:
        st.session_state.current_page = "manager"
        st.rerun()
