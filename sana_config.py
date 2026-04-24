# sana_config.py
import core_seed

DEFAULT_API_KEY = ""

# 引入外部種子，達成複寫需求
MODULES_FOR_UI = core_seed.MODULES_FOR_UI
SYSTEM_PROMPT = core_seed.SYSTEM_PROMPT

def get_forced_template(user_input):
    """產生強制防偷懶的注入模板 (對應英文 VFO)"""
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
