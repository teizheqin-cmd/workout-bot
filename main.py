import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from gemini_helper import analyze_workout
from excel_helper import append_workout_row, get_summary

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💪 Workout Bot 已启动！\n\n"
        "直接发你的运动记录给我，我会帮你：\n"
        "  • 分析并记录到 Excel\n"
        "  • 给你专业反馈\n\n"
        "命令：\n"
        "  /summary — 查看最近10次运动记录\n"
        "  /help — 帮助\n\n"
        "例子：\n"
        "_今天练胸，卧推4组10下80kg，飞鸟3组12下15kg，跑步20分钟_",
        parse_mode="Markdown"
    )

# ─── /help ────────────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *使用方法*\n\n"
        "直接发你的运动内容，格式随意，例如：\n\n"
        "• 今天深蹲4x10 100kg，硬拉3x8 120kg\n"
        "• Chest day: bench press 4x10 80kg, flyes 3x12 15kg\n"
        "• 跑步45分钟，心率150，距离8km\n\n"
        "我会自动提取数据并给你分析反馈 💬",
        parse_mode="Markdown"
    )

# ─── /summary ─────────────────────────────────────────────────────────────────
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ 正在读取你的运动记录...")
    try:
        text = get_summary()
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 读取失败：{e}")

# ─── 处理运动消息 ──────────────────────────────────────────────────────────────
async def handle_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.reply_text("⏳ 正在分析你的运动记录...")

    try:
        # 1. Gemini 分析
        result = analyze_workout(user_message)

        # 2. 写入 Excel
        append_workout_row(result, user_message)

        # 3. 回复用户
        reply = (
            f"✅ *已记录！*\n\n"
            f"📅 日期：{result['date']}\n"
            f"🏋️ 类型：{result['workout_type']}\n"
            f"⏱️ 时长：{result['duration']}\n"
            f"📝 动作：{result['exercises_summary']}\n\n"
            f"💬 *Gemini 反馈：*\n{result['feedback']}"
        )
        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(f"❌ 出错了：{e}\n\n请再试一次。")

# ─── 主程序 ───────────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_workout))

    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
