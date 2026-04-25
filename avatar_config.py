import core_seed

DEFAULT_API_KEY = ""

# 引入底層系統防禦與運作邏輯
BASE_SYSTEM_RULES = core_seed.BASE_SYSTEM_RULES

def get_forced_template(user_input):
    """產生強制防偷懶的注入模板，確保模型遵守 VFO 內部推演格式"""
    return f"""{user_input}

【SYSTEM MANDATORY OVERRIDE】
You MUST strictly follow the 【VFO Formatted Output Template】 below for your internal reasoning before outputting the final reply. DO NOT SKIP ANY STEPS.

[Pre-State Loading]
...
[Step One]
...
[Step Two]
...
[VFO Harmonized Decision]
...
[Final Reply]
...
[Stage 0: Round Settlement & Next Round Strategic Precipitation]
...
----------------------
[Final Reply]
(Character body language/expression/action)
「Character spoken lines」
(Character body language/expression/action after speaking)"""
