import os
import json
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1XYuRrCBIt6-cMFj6uE_fm1r7tMec-h0RX-JXtyOk8Rw"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = ["Date", "Workout Type", "Duration", "Exercises Summary",
           "Total Volume (kg)", "Intensity", "Feedback", "Original Message"]

def _get_sheet():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not set")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    ws = spreadsheet.sheet1
    if ws.row_count == 0 or ws.cell(1, 1).value != "Date":
        ws.insert_row(HEADERS, 1)
        spreadsheet.batch_update({
            "requests": [{
                "repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.18, "green": 0.25, "blue": 0.34},
                            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            }]
        })
    return ws

def get_recent_history(limit: int = 5) -> str:
    """Get last N workouts as text for Gemini context"""
    try:
        ws = _get_sheet()
        all_rows = ws.get_all_values()
        data_rows = all_rows[1:] if len(all_rows) > 1 else []
        if not data_rows:
            return ""
        last_n = data_rows[-limit:]
        lines = []
        for row in last_n:
            date_val  = row[0] if len(row) > 0 else "?"
            wtype     = row[1] if len(row) > 1 else "?"
            duration  = row[2] if len(row) > 2 else "?"
            exercises = row[3] if len(row) > 3 else "?"
            volume    = row[4] if len(row) > 4 else "0"
            intensity = row[5] if len(row) > 5 else "?"
            original  = row[7] if len(row) > 7 else ""
            lines.append(
                f"[{date_val}] {wtype} | {duration} | {intensity} | Vol: {volume}kg\n"
                f"动作: {exercises}\n"
                f"原始记录: {original}\n"
            )
        return "\n---\n".join(lines)
    except Exception:
        return ""

def append_workout_row(result: dict, raw_input: str):
    ws = _get_sheet()
    row = [
        result.get("date", ""),
        result.get("workout_type", ""),
        result.get("duration", ""),
        result.get("exercises_summary", ""),
        result.get("total_volume_kg", 0),
        result.get("intensity", ""),
        result.get("feedback", ""),
        raw_input
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")

def get_summary() -> str:
    ws = _get_sheet()
    all_rows = ws.get_all_values()
    data_rows = all_rows[1:] if len(all_rows) > 1 else []
    if not data_rows:
        return "📭 还没有任何运动记录！发送你的第一次运动吧 💪"
    last_10 = data_rows[-10:]
    lines = ["📊 *最近运动记录*\n"]
    for row in reversed(last_10):
        date_val  = row[0] if len(row) > 0 else "?"
        wtype     = row[1] if len(row) > 1 else "?"
        duration  = row[2] if len(row) > 2 else "?"
        volume    = row[4] if len(row) > 4 else "0"
        intensity = row[5] if len(row) > 5 else "?"
        lines.append(f"📅 `{date_val}` | {wtype} | {duration} | Vol: {volume}kg | {intensity}")
    total = len(data_rows)
    lines.append(f"\n_共 {total} 次记录_")
    return "\n".join(lines)
