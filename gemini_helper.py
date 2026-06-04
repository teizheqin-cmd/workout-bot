import os
import json
import re
from datetime import date
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM_PROMPT = """You are a fitness coach assistant. The user will send you their workout log in any language (English, Chinese, Malay, or mixed).

Your job:
1. Extract structured workout data
2. Give personalized, motivating feedback in THE SAME LANGUAGE the user wrote in

Respond ONLY with a JSON object, no markdown, no explanation:
{
  "workout_type": "e.g. Chest Day / Leg Day / Cardio / Full Body / etc",
  "duration": "e.g. 60 min (estimate if not given)",
  "exercises_summary": "brief summary of exercises, sets, reps, weight",
  "total_volume_kg": "estimated total volume in kg (sets x reps x weight), put 0 if cardio only",
  "intensity": "Low / Medium / High",
  "feedback": "2-3 sentences of personalized coaching feedback in the SAME language as the user's message. Be specific, encouraging, and give 1 actionable tip."
}"""

def analyze_workout(user_message: str) -> dict:
    prompt = f"{SYSTEM_PROMPT}\n\nUser workout log:\n{user_message}"
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    data["date"] = date.today().isoformat()
    data["raw_input"] = user_message
    return data
