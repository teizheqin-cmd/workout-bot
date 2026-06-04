import os
import json
import re
from datetime import date
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

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

COACH_PERSONA = """你是 Brandon 的私人健身教练，名字叫 Coach Lee。
你了解 Brandon 的目标和训练背景。
风格：专业、鼓励、实际、直接。
永远用 Brandon 写消息的语言回复（中文/英文/混合）。
"""

WORKOUT_PROMPT = f"""{COACH_PERSONA}
{USER_PROFILE}

Brandon 刚发来他的运动记录，以及他过去的运动历史。

你的任务是给出完整的教练反馈，格式如下（用 Brandon 写的语言）：

📊 **本次训练总结**
简短说明这次做了什么，训练类型和强度。

📈 **对比上次 / 进步分析**
跟历史记录对比，哪里进步了？哪里退步了？如果是第一次记录就说"这是你的第一次记录，以后会有对比"。

✅ **做得好的地方**
具体说出这次训练哪里做得好，为什么好。

⚠️ **需要注意的地方**
姿势、休息、频率、强度等方面需要注意什么。

🎯 **下次可以改进的地方**
1-2个具体可执行的改进建议，针对他的目标（减脂/肩膀/体态）。

💡 **教练额外建议**
营养、恢复、训练计划或其他重要建议。

最后用一句鼓励的话结尾。

Respond ONLY with a JSON object, no markdown, no explanation:
{{
  "workout_date": "从用户消息提取运动日期，格式YYYY-MM-DD。如果用户说'今天'就用今天，如果说'5月28号'就填对应日期，如果说'昨天'就用昨天的日期。今天是{date.today().isoformat()}",
  "workout_type": "训练类型",
  "duration": "时长",
  "exercises_summary": "动作摘要",
  "total_volume_kg": "总训练量kg，纯有氧填0",
  "intensity": "Low / Medium / High",
  "feedback": "按照上面格式的完整教练反馈，包含所有6个部分"
}}"""

CHAT_PROMPT = f"""{COACH_PERSONA}
{USER_PROFILE}

Brandon 问了你一个问题。以私人教练身份回答：
- 专业、实际、针对他的目标和新手水平
- 回答要完整但不啰嗦
- 如果跟减脂/肩膀/体态有关，给更具体的建议
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
    history_section = f"\n\nBrandon 过去的运动记录：\n{history}" if history else "\n\n（这是 Brandon 的第一次运动记录，没有历史对比）"
    prompt = f"{WORKOUT_PROMPT}{history_section}\n\n今次运动记录：\n{user_message}"
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    # Use date from message if Gemini extracted it, otherwise use today
    data["date"] = data.pop("workout_date", date.today().isoformat())
    data["raw_input"] = user_message
    return data

def answer_question(user_message: str) -> str:
    prompt = f"{CHAT_PROMPT}\n\nBrandon 的问题：{user_message}"
    response = model.generate_content(prompt)
    return response.text.strip()
