import streamlit as st
import avatar_config as cfg
import avatar_engine as engine
import avatar_presets as presets # 引入內建人格庫
import re

# ==========================================
# 1. 狀態與路由初始化
# ==========================================
st.set_page_config(page_title="Project AVATAR 認知終端", layout="wide", initial_sidebar_state="expanded")

if "current_page" not in st.session_state:
    st.session_state.current_page = "manager"
if "avatars" not in st.session_state:
    st.session_state.avatars = {}
if "active_avatar_name" not in st.session_state:
    st.session_state.active_avatar_name = None
if "available_models" not in st.session_state:
    st.session_state.available_models = []
    
# 用於管理建立人物時的暫存標籤 (Seeds)
if "temp_seeds" not in st.session_state:
    st.session_state.temp_seeds = []

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
# 3. 頁面 1：人物建檔與管理庫
# ==========================================
def render_manager_page():
    st.title("🌌 Project AVATAR - 人格容器庫")
    st.markdown("在此建立新的意識容器，或載入內建人格進行深度模擬。")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("➕ 建立新容器 (New Avatar)")
        
        # --- 基本資料區 ---
        a_name = st.text_input("人物代號 (Name)*", placeholder="例如：Alex")
        col_a, col_g = st.columns(2)
        with col_a:
            a_age = st.number_input("年齡", min_value=1, max_value=120, value=33)
        with col_g:
            a_gender = st.selectbox("性別", ["男性", "女性", "非二元", "保密"])
            
        st.divider()
        
        # --- 種子標籤管理區 (逐一確認/刪除) ---
        st.markdown("##### 🌱 注入靈魂種子 (特質/設定)")
        col_seed_in, col_seed_btn = st.columns([7, 3])
        with col_seed_in:
            new_seed = st.text_input("輸入單一特質", placeholder="例如：個性機車", key="seed_input_box", label_visibility="collapsed")
        with col_seed_btn:
            if st.button("➕ 加入種子", use_container_width=True):
                if new_seed and new_seed not in st.session_state.temp_seeds:
                    st.session_state.temp_seeds.append(new_seed)
                    st.rerun()
                    
        # 顯示並提供刪除功能的標籤列表
        if st.session_state.temp_seeds:
            st.write("**已加入的種子：**")
            for i, seed in enumerate(st.session_state.temp_seeds):
                sc1, sc2 = st.columns([8, 2])
                sc1.info(f"🏷️ {seed}")
                if sc2.button("❌ 刪除", key=f"del_seed_{i}", use_container_width=True):
                    st.session_state.temp_seeds.pop(i)
                    st.rerun()
            st.divider()
            # 👇 新增：選擇核心種子
            core_seed_label = st.selectbox("⭐ 選定核心種子 (僅供 UI 標示)", st.session_state.temp_seeds)
        else:
            st.caption("尚未加入任何特質種子。")
            core_seed_label = "未設定"
            
        st.divider()

        # --- 生成矩陣與存檔按鈕 ---
        if st.button("🚀 注入靈魂並生成矩陣", type="primary", use_container_width=True):
            if not api_key or not selected_model:
                st.error("請先在側邊欄設定 API Key 與模型。")
            elif not a_name:
                st.error("請填寫人物代號！")
            elif a_name in st.session_state.avatars:
                st.error("此代號已存在，請換一個名字。")
            else:
                first_seed = f"{a_age}歲{a_gender}"
                all_seeds = [first_seed] + st.session_state.temp_seeds
                
                with st.spinner("正在編譯核心模塊矩陣 (這可能需要幾十秒)..."):
                    try:
                        generated_matrix = engine.generate_avatar_matrix(api_key, selected_model, all_seeds)
                        st.session_state.avatars[a_name] = {
                            "name": a_name,
                            "first_seed": first_seed,
                            "core_seed_label": core_seed_label, # 存入核心標籤
                            "seeds": list(st.session_state.temp_seeds),
                            "matrix": generated_matrix,
                            "messages": [], 
                            "scene": "我們現在正在進行一場普通的初次見面談話。",
                            "user_perception": "一位剛認識的普通陌生人。",
                            "core_target": "維持基本社交禮儀，完成這次對話。(強度：低)"
                        }
                        # 清空暫存
                        st.session_state.temp_seeds = []
                        st.success(f"✅ {a_name} 意識容器建立完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"矩陣生成失敗: {str(e)}")

    with col2:
        st.subheader("📂 已存檔與內建容器")
        
        # 載入內建按鈕
        if st.button("✨ 載入內建範例人格：唐銘駿", use_container_width=True):
            if "唐銘駿" not in st.session_state.avatars:
                st.session_state.avatars["唐銘駿"] = presets.PRESETS["唐銘駿"]
                st.success("唐銘駿已載入資料庫！")
                st.rerun()
            else:
                st.info("唐銘駿已經在資料庫中了。")
                
        st.divider()

        if not st.session_state.avatars:
            st.info("目前沒有任何人物檔案。請在左側建立或載入內建人格。")
        else:
            for name, data in st.session_state.avatars.items():
                with st.expander(f"👤 {name} ({data['first_seed']} / 核心: {data.get('core_seed_label', '無')})", expanded=True):
                    st.caption(f"附加種子: {', '.join(data['seeds']) if data['seeds'] else '無'}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"▶️ 進入模擬", key=f"sim_{name}", type="primary"):
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
    core_label = avatar_data.get('core_seed_label', '未設定') # 讀取核心標籤
    
    # --- 頂部導航與標題 ---
    col_nav1, col_nav2, col_nav3 = st.columns([1, 8, 1])
    with col_nav1:
        if st.button("⬅️ 返回人物庫"):
            st.session_state.current_page = "manager"
            st.rerun()
    with col_nav2:
        # 修改後的標題格式
        st.markdown(f"### 🧠 測試對象：**{avatar_name}** | {avatar_data['first_seed']} / 核心: {core_label}")
    with col_nav3:
        # 新增刷新對話按鈕
        if st.button("🔄 刷新對話", type="primary"):
            st.session_state.avatars[avatar_name]["messages"] = []
            st.rerun()

    # ==========================================
    # --- 置頂橫列監測板 (Dashboard) ---
    # ==========================================
    st.subheader(f"📊 {avatar_name} 監測板")
    
    latest_msg = None
    if avatar_data["messages"]:
        for msg in reversed(avatar_data["messages"]):
            if msg["role"] == "assistant":
                latest_msg = msg
                break
                
    if latest_msg and latest_msg.get("parsed_dash"):
        d = latest_msg["parsed_dash"]
        
        # 1. 橫列 5 欄核心數值
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        with col_m1:
            st.metric("L (好感度)", d.get("l_val", "0").split('(')[0].strip())
        with col_m2:
            st.metric("SAI (地位感知)", d.get("sai", "50").split('(')[0].strip())
        with col_m3:
            st.metric("T (信任度)", d.get("t_val", "0").split('(')[0].strip())
        with col_m4:
            st.metric("B-D (邊界防禦)", d.get("bd", "100").split('(')[0].strip())
        with col_m5:
            # 處理 MF，將純數字與後方的原因切開
            mf_full = d.get('mf', '20')
            mf_val = mf_full.split('(')[0].strip()
            st.metric("MF (面具疲勞)", mf_val)

        # 2. 面具疲勞度詳細解析 & 圖靈防禦機制
        mf_reason = mf_full[len(mf_val):].strip() # 擷取包括括號在內的增減與狀態
        st.markdown(f"**🎭 面具疲勞度 (MF): {mf_val} / 100** {mf_reason}")
        
        ai_scan = d.get("ai_scan", "0")
        if ai_scan != "0" and ai_scan != "No Data":
            st.error(f"🛡️ 圖靈測試防禦機制啟動：⚠️ 偵測到 AI 塑膠味！入侵值: {ai_scan}")
            
        # 3. 將文字較多的模組收納進 Expander 以免佔用主畫面高度
        with st.expander("🔍 展開詳細心理模組推演", expanded=False):
            st.markdown("**🧠 模組 B: 戰略判斷 (Introspection)**")
            st.info(d.get("mod_b", "無資料"))
            
            st.markdown("**🌋 模組 C: 真實內在反射 (True Inner Reflex)**")
            st.warning(d.get("mod_c", "無資料"))
            
            st.markdown("**🎭 模組 D: 職業面具偽裝 (Professional Mask)**")
            st.success(d.get("mod_d", "無資料"))
            
            st.markdown("**🎯 模組 A: 次輪準備 (Next Round Prep)**")
            st.write(d.get("mod_a", "無資料"))
            
            st.divider()
            st.caption("⚙️ 開發者底層監控 (Raw Data)")
            st.code(latest_msg.get("raw_text", "無資料"), language="markdown")
    else:
        st.caption("等待首輪對話產生 VFO 數據...")

    st.divider()
    
    # ==========================================
    # --- 設定區與聊天區塊 (改為全寬) ---
    # ==========================================
    with st.expander("⚙️ 動態環境、視角與動機設定 (可隨時修改，下回合生效)", expanded=False):
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            new_scene = st.text_area("🎬 當下場景與客觀前提", value=avatar_data['scene'], height=100, help="你們在哪裡？正在發生什麼事？")
        with col_s2:
            new_perception = st.text_area("👁️ Avatar 眼中的你 (狀態/外貌/身分)", value=avatar_data.get('user_perception', ''), height=100, help="Avatar 目前認定你是什麼身分？")
        with col_s3:
            new_target = st.text_area("🎯 Avatar 初始/核心目標與強度", value=avatar_data.get('core_target', ''), height=100, help="Avatar 當下最想達成的目的是什麼？")
            
        # 即時儲存設定
        if new_scene != avatar_data['scene']: st.session_state.avatars[avatar_name]['scene'] = new_scene
        if new_perception != avatar_data.get('user_perception'): st.session_state.avatars[avatar_name]['user_perception'] = new_perception
        if new_target != avatar_data.get('core_target'): st.session_state.avatars[avatar_name]['core_target'] = new_target

    st.divider()

    # 渲染對話紀錄
    for msg in avatar_data['messages']:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    # 使用者輸入與運算邏輯
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
                    
                    dynamic_system_prompt = (
                        avatar_data['matrix'] + "\n\n" + 
                        cfg.BASE_SYSTEM_RULES + 
                        f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                        f"🎬 1. 互動場景與前提：\n{avatar_data['scene']}\n\n"
                        f"👁️ 2. {avatar_name} 眼中的使用者狀態 (外貌/身分/客觀評估)：\n{avatar_data['user_perception']}\n\n"
                        f"🎯 3. {avatar_name} 當下的核心目標 (Core Target) 與驅動強度：\n{avatar_data['core_target']}\n"
                        f"(⚠️ VFO 引擎指令：請將上述 Target 強制寫入並覆蓋初始 Core Target，且在 Step 1 戰略判斷中，必須嚴格受此 Target 強度與使用者狀態所驅動。)"
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
