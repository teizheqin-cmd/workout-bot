import logging
import os
import sys
import traceback
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", 10000))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

def main():
    print("=== STARTUP DEBUG ===", flush=True)
    print(f"BOT_TOKEN set: {bool(BOT_TOKEN)}", flush=True)

    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set!", flush=True)
        sys.exit(1)

    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    print("Health server started", flush=True)

    try:
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
        from telegram import Update
        from telegram.ext import ContextTypes
        print("Telegram imported OK", flush=True)
    except Exception as e:
        print(f"ERROR importing telegram: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    try:
        from gemini_helper import analyze_workout, answer_question, classify_message
        print("Gemini imported OK", flush=True)
    except Exception as e:
        print(f"ERROR importing gemini_helper: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    try:
        from sheets_helper import append_workout_row, get_summary, get_recent_history
        print("Sheets imported OK", flush=True)
    except Exception as e:
        print(f"ERROR importing sheets_helper: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "💪 Coach Lee 准备好了！\n\n"
            "我是你的私人健身教练，我可以：\n\n"
            "📝 记录运动 — 发你的运动记录给我\n"
            "📊 对比分析 — 跟你之前的训练对比\n"
            "💬 回答问题 — 任何健身、营养问题\n"
            "📈 查看记录 — /summary\n\n"
            "来吧，把你的运动发给我！💪"
        )

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📋 使用方法\n\n"
            "📝 记录运动：\n"
            "直接发运动内容，例如：\n"
            "今天深蹲4x10 100kg，跑步30分钟\n\n"
            "💬 问健身问题：\n"
            "直接问，例如：\n"
            "我想减脂应该怎么吃？\n"
            "肩膀怎么练比较有效？\n\n"
            "📊 查看记录：/summary"
        )

    async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ 读取中...")
        try:
            text = get_summary()
            await update.message.reply_text(text)
        except Exception as e:
            await update.message.reply_text(f"❌ 读取失败：{e}")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        await update.message.reply_text("⏳ Coach Lee 正在分析...")

        try:
            msg_type = classify_message(user_message)

            if msg_type == "workout_log":
                history = get_recent_history()
                result = analyze_workout(user_message, history)
                append_workout_row(result, user_message)
                reply = (
                    f"✅ 已记录！\n\n"
                    f"📅 {result['date']} | 🏋️ {result['workout_type']} | "
                    f"⏱️ {result['duration']} | 💪 {result['intensity']}\n\n"
                    f"{result['feedback']}"
                )
            else:
                answer = answer_question(user_message)
                reply = f"🏋️ Coach Lee：\n\n{answer}"

            # Split if message too long
            if len(reply) > 4000:
                parts = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
                for part in parts:
                    await update.message.reply_text(part)
            else:
                await update.message.reply_text(reply)

        except Exception as e:
            logging.error(f"Error: {e}")
            await update.message.reply_text(f"❌ 出错了：{e}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Starting polling mode...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
