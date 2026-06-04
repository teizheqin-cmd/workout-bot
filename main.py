import logging
import os
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
RENDER_URL = os.environ.get("RENDER_URL", "").strip()
PORT = int(os.environ.get("PORT", 8080))

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
    print(f"RENDER_URL: {RENDER_URL}", flush=True)
    print(f"PORT: {PORT}", flush=True)

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
        from gemini_helper import analyze_workout
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
        await update.message.reply_text("💪 Workout Bot 已启动！直接发运动记录给我吧。")

    async def handle_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        await update.message.reply_text("⏳ 正在分析...")
        try:
            result = analyze_workout(user_message)
            append_workout_row(result, user_message)
            reply = (
                f"✅ *已记录！*\n\n"
                f"📅 {result['date']}\n"
                f"🏋️ {result['workout_type']}\n"
                f"⏱️ {result['duration']}\n"
                f"📝 {result['exercises_summary']}\n\n"
                f"💬 *反馈：*\n{result['feedback']}"
            )
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ 出错了：{e}")

    async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ 读取中...")
        try:
            text = get_summary()
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ 读取失败：{e}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_workout))

    if RENDER_URL:
        print("Starting webhook mode...", flush=True)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        print("Starting polling mode...", flush=True)
        app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
