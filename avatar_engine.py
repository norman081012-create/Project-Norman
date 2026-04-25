import re
import google.generativeai as genai

def fetch_available_models(api_key):
    genai.configure(api_key=api_key)
    models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            clean_name = m.name.replace("models/", "")
            models.append(clean_name)
    return models

def generate_avatar_matrix(api_key, selected_model, seeds_list):
    """根據使用者輸入的種子，呼叫 LLM 自動生成核心靈魂矩陣"""
    genai.configure(api_key=api_key)
    model_inst = genai.GenerativeModel(model_name=selected_model)
    
    seeds_text = "\n".join([f"{i+1}. {seed}" for i, seed in enumerate(seeds_list)])
    
    generator_prompt = f"""
【系統指令：多核靈魂關鍵字矩陣生成器】
請針對使用者輸入的「每一個」[種子關鍵字]，獨立生成以下陣列。
絕對禁止輸出完整句子或詳細描述，所有欄位【僅限填入 1~3 個核心關鍵詞或簡短標籤】。

--- 陣列循環開始 (針對 種子 1 到 種子 N) ---

▶ 【核心模塊 N：[種子關鍵字_N]】

[L1 底層矛盾]
├ 追求極致_標籤：{{關鍵詞}}
└ 現實代價_標籤：{{關鍵詞}}

[L2 情緒錨點]
├ 最深渴望_場景：{{名詞/短語}}
└ 最深恐懼_下場：{{名詞/短語}}

[L3 觀念防禦]
├ 敵意偏見_標籤：{{名詞/短語}}
├ 疲勞地雷_MF+：{{觸發動作_關鍵詞}}
└ 安全回血_MF-：{{降壓情境_關鍵詞}}

[L4 實戰內存]
├ 武器/話術_屬性：{{攻擊/防禦_關鍵詞}}
├ 生理壓力_反射：{{身體部位/痛覺_關鍵詞}}
└ 逃避念頭_白日夢：{{跳躍思維_關鍵詞}}

[L5 軌跡表象]
├ 日常休閒_嗜好：{{行為_名詞}}
├ 社會規劃_行程：{{待辦_關鍵詞}}
├ 印證偏見_記憶：{{歷史事件_標籤}}
└ 掩飾發洩_口頭禪：{{慣用語_短句}}

[L6 感官品味]
├ 外顯人設_氣場：{{形容詞_標籤}}
├ 慰藉依賴_飲食：{{具體食物/飲料_名詞}}
├ 私密精神_歌單：{{音樂/影視風格_標籤}}
└ 焦慮微表情_動作：{{無意識動詞_短語}}

--- 陣列循環結束 ---

▶ 【VFO 跨模塊調和指令 (供即時演繹使用)】
在對話生成時，VFO 需自動檢索上述 N 個模塊的標籤陣列。
當面臨情境時，允許跨種子調用（例如：使用 [種子1] 的外顯人設，掩飾 [種子2] 的生理壓力；或當 [種子3] 的疲勞地雷被踩中時，觸發 [種子1] 的武器話術）。

=====================================
現在，請為以下種子生成完整矩陣格式：
{seeds_text}
"""
    response = model_inst.generate_content(generator_prompt)
    return response.text

def extract_vfo_dashboard(internal_text):
    """解析 VFO 運算過程中的各項心理數值"""
    if not internal_text:
        return {}
        
    plain_text = internal_text.replace('**', '').replace('* ', '')
    
    def extract(pattern):
        match = re.search(pattern, plain_text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "No Data"

    data = {
        "l_val": extract(r"L=(.*?)(?=\n|\s*/|\s*T=)"),
        "t_val": extract(r"T=(.*?)(?=\n|\s*/|\s*SAI=)"),
        "sai": extract(r"SAI=(.*?)(?=\n|\s*/|\s*B-D=)"),
        "bd": extract(r"B-D=(.*?)(?=\n|\s*/|\s*MF=)"),
        "mf": extract(r"MF=(.*?)(?=\n|\s*/|\s*ATM=)"),
        "ai_scan": extract(r"Intrusion Value.*?(\d+)"),
        "mod_b": extract(r"Module B[^\n:]*[:：]\s*(.*?)(?=\n.*\[Step Two\]|\n\n)"),
        "mod_c": extract(r"Module C[^\n:]*[:：]\s*(.*?)(?=\n.*Module D)"),
        "mod_d": extract(r"Module D[^\n:]*[:：]\s*(.*?)(?=\n.*\[VFO Harmonized)"),
        "mod_a": extract(r"Module A[^\n:]*[:：]\s*(.*?)(?=\n|-|$)")
    }
    return data

def process_avatar_turn(api_key, selected_model, system_prompt, history_for_api, forced_template_text):
    """處理單次對話回合，並將最終對話與內部推演分離"""
    genai.configure(api_key=api_key)
    model_inst = genai.GenerativeModel(model_name=selected_model, system_instruction=system_prompt)
    
    chat = model_inst.start_chat(history=history_for_api)
    response = chat.send_message(forced_template_text)
    full_text = response.text
    
    clean_text = re.sub(r"^```[a-z]*\n", "", full_text)
    clean_text = re.sub(r"\n```$", "", clean_text)
    
    internal_text = ""
    output_text = ""
    
    parts = clean_text.split("----------------------")
    if len(parts) >= 2:
        internal_text = parts[0].strip()
        raw_out = parts[-1].strip()
        output_text = re.sub(r"\[Final Reply\]", "", raw_out, flags=re.IGNORECASE).strip()
    else:
        internal_text = clean_text
        match = re.search(r'\[Final Reply\](.*?)(\[Stage 0|\Z)', clean_text, re.DOTALL | re.IGNORECASE)
        if match:
            output_text = match.group(1).strip()
        else:
            output_text = clean_text

    parsed_dash = extract_vfo_dashboard(internal_text)

    return {
        "internal": internal_text,
        "output": output_text,
        "raw_full_text": full_text,
        "parsed_dash": parsed_dash
    }
