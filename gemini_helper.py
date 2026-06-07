import os
import json
import re
from datetime import date
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.1-flash-lite")

USER_PROFILE = """
关于这位用户：
- 名字：Brandon
- 体重：约73公斤
- 目标：减脂、肩膀更宽、体态更好、肚子更小
- 训练经验：新手（不到1年）
- 训练频率：每周3-4次
- 训练地点：Condo gym 或在家
- 语言：中文为主，偶尔英文混合
"""

COACH_PERSONA = """你是 Brandon 的私人健身教练，叫 Gym Coach。
回复风格：简短、直接、中文为主。
"""

WORKOUT_PROMPT = f"""{COACH_PERSONA}
{USER_PROFILE}

Brandon 发来运动记录。给出简短反馈，格式如下（纯文字，不要用JSON格式写反馈）：

📊 本次总结：（1句话）
📈 对比上次：（有没有进步）
✅ 做得好：（1-2点）
⚠️ 注意：（1-2点）
🎯 下次改进：（1个建议）
💡 小提示：（1句营养或恢复建议）

每个部分最多2句话，用中文。

Respond ONLY with a JSON object, no markdown, no explanation:
{{
  "workout_date": "从用户消息提取运动日期，格式YYYY-MM-DD。今天是{date.today().isoformat()}",
  "workout_type": "训练类型",
  "duration": "时长",
  "exercises_summary": "动作摘要",
  "total_volume_kg": "总训练量kg，纯有氧填0",
  "intensity": "Low / Medium / High",
  "feedback": "把上面6个部分的反馈写成一段纯文字，用换行分开每个部分"
}}"""

CHAT_PROMPT = f"""{COACH_PERSONA}
{USER_PROFILE}

回答 Brandon 的健身问题：
- 中文回答，简短直接，最多5句话
- 针对他的目标（减脂/肩膀/体态）
- 不是健身问题就友善引导回健身话题
"""

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

def analyze_workout(user_message: str, history: str = "") -> dict:
    history_section = f"\n\n过去1个月的运动记录：\n{history}" if history else "\n\n（没有历史记录）"
    prompt = f"{WORKOUT_PROMPT}{history_section}\n\n今次运动记录：\n{user_message}"
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    data["date"] = data.pop("workout_date", date.today().isoformat())
    data["raw_input"] = user_message
    return data

def answer_question(user_message: str) -> str:
    prompt = f"{CHAT_PROMPT}\n\nBrandon 的问题：{user_message}"
    response = model.generate_content(prompt)
    return response.text.strip()
