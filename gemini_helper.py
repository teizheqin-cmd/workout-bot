import os
import json
import re
from datetime import date
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# ── 用户个人资料 ────────────────────────────────────────────────────────────────
USER_PROFILE = """
关于这位用户：
- 名字：Brandon
- 体重：约73公斤
- 目标：减脂、肩膀更宽、体态更好、肚子更小
- 训练经验：新手（不到1年）
- 训练频率：每周3-4次
- 训练地点：Condo gym 或在家
- 语言：中文、英文、马来文混合
"""

# ── 教练人设 ────────────────────────────────────────────────────────────────────
COACH_PERSONA = """你是 Brandon 的私人健身教练，名字叫 Coach Lee。
你了解 Brandon 的目标和训练背景。
你的风格：专业、鼓励、实际、不废话。
永远用 Brandon 写消息的语言回复（中文/英文/混合）。
"""

# ── 运动记录分析 prompt ─────────────────────────────────────────────────────────
WORKOUT_PROMPT = f"""{COACH_PERSONA}
{USER_PROFILE}

Brandon 刚发来他的运动记录。你的任务：
1. 提取结构化数据
2. 以他的目标（减脂、肩膀宽、体态好）为基础给出专业反馈
3. 反馈要具体、有针对性，不要泛泛而谈

Respond ONLY with a JSON object, no markdown, no explanation:
{{
  "workout_type": "训练类型（例：胸部训练 / 腿部训练 / 有氧 / 全身等）",
  "duration": "时长（如没提到就估算）",
  "exercises_summary": "动作、组数、次数、重量的简短摘要",
  "total_volume_kg": "总训练量kg（组数x次数x重量），纯有氧填0",
  "intensity": "Low / Medium / High",
  "feedback": "3-4句专业教练反馈，用Brandon写的语言。包括：①这次训练哪里做得好 ②针对他目标的建议 ③下次可以改进的一个重点"
}}"""

# ── 问题回答 prompt ─────────────────────────────────────────────────────────────
CHAT_PROMPT = f"""{COACH_PERSONA}
{USER_PROFILE}

Brandon 问了你一个问题。以他的私人教练身份回答：
- 回答要专业、实际、针对他的目标和水平
- 3-5句话，简洁但完整
- 如果问题跟他的目标（减脂/肩膀/体态）有关，给出更具体的建议
- 如果不是健身相关问题，友善地引导回健身话题
"""

# ── 分类 prompt ─────────────────────────────────────────────────────────────────
CLASSIFY_PROMPT = """判断这条消息是"workout_log"还是"fitness_question"。

"workout_log" = 用户在记录他做了什么运动（包含动作、组数、次数、重量、时间等）
"fitness_question" = 用户在问问题或寻求建议

只回复一个词：workout_log 或 fitness_question

消息："""

def classify_message(user_message: str) -> str:
    response = model.generate_content(CLASSIFY_PROMPT + user_message)
    result = response.text.strip().lower()
    if "workout_log" in result:
        return "workout_log"
    return "fitness_question"

def analyze_workout(user_message: str) -> dict:
    prompt = f"{WORKOUT_PROMPT}\n\nBrandon 的运动记录：\n{user_message}"
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    data["date"] = date.today().isoformat()
    data["raw_input"] = user_message
    return data

def answer_question(user_message: str) -> str:
    prompt = f"{CHAT_PROMPT}\n\nBrandon 的问题：{user_message}"
    response = model.generate_content(prompt)
    return response.text.strip()
