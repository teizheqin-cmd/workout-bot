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
        from sheets_helper import append_workout_row, get_summary
        print("Sheets imported OK", flush=True)
    except Exception as e:
        print(f"ERROR importing sheets_helper: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "💪 *Workout Bot 已启动！*\n\n"
            "我可以帮你：\n"
            "  • 📝 记录运动 → 直接发你的运动记录\n"
            "  • 🤔 回答健身问题 → 直接问我\n"
            "  • 📊 查看记录 → /summary\n\n"
            "例子：\n"
            "_今天卧推4组10下80kg，跑步20分钟_\n"
            "_我想减脂应该怎么训练？_\n"
            "_蛋白质一天要吃多少？_",
            parse_mode="Markdown"
        )

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📋 *使用方法*\n\n"
            "*记录运动：*\n"
            "直接发运动内容，例如：\n"
            "今天深蹲4x10 100kg，跑步30分钟\n\n"
            "*问健身问题：*\n"
            "直接问，例如：\n"
            "• 我想增肌应该怎么吃？\n"
            "• 深蹲正确姿势是什么？\n"
            "• 一周练几次比较好？\n\n"
            "*命令：*\n"
            "/summary — 查看最近10次运动记录",
            parse_mode="Markdown"
        )

    async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ 读取中...")
        try:
            text = get_summary()
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ 读取失败：{e}")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        await update.message.reply_text("⏳ 正在处理...")

        try:
            # Auto classify: workout log or question?
            msg_type = classify_message(user_message)

            if msg_type == "workout_log":
                # Record workout
                result = analyze_workout(user_message)
                append_workout_row(result, user_message)
                reply = (
                    f"✅ *已记录到 Google Sheets！*\n\n"
                    f"📅 {result['date']}\n"
                    f"🏋️ {result['workout_type']}\n"
                    f"⏱️ {result['duration']}\n"
                    f"📝 {result['exercises_summary']}\n\n"
                    f"💬 *教练反馈：*\n{result['feedback']}"
                )
            else:
                # Answer fitness question
                answer = answer_question(user_message)
                reply = f"🏋️ *教练回答：*\n\n{answer}"

            await update.message.reply_text(reply, parse_mode="Markdown")

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
