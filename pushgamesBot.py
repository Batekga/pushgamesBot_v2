import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import json
import os

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DATA_FILE = 'pushup_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_today_str():
    return datetime.now().strftime('%Y-%m-%d')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для учёта отжиманий.\n"
        "Используй команды:\n"
        "/push <число> — добавить подход\n"
        "/stats — статистика за сегодня\n"
        "/log — подробности подходов\n"
        "/help — помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/push <число> — добавить подход с повторениями\n"
        "/stats — текущий прогресс\n"
        "/log — подробности подходов"
    )

async def push(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.first_name or user.username or "Аноним"
    args = context.args

    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажи количество повторений через пробел, например:\n/push 25")
        return

    count = int(args[0])
    if count <= 0:
        await update.message.reply_text("Количество должно быть положительным числом.")
        return

    data = load_data()
    today = get_today_str()

    if today not in data:
        data[today] = {}

    if username not in data[today]:
        data[today][username] = []

    data[today][username].append(count)
    save_data(data)

    total_today = sum(data[today][username])

    await update.message.reply_text(
        f"{username}: добавлено {count} повторений.\n"
        f"Итого сегодня: {total_today} отжиманий."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = get_today_str()

    if today not in data or not data[today]:
        await update.message.reply_text("Сегодня ещё нет данных.")
        return

    lines = [f"📊 Статистика за {today}:"]
    for user, reps_list in data[today].items():
        total = sum(reps_list)
        done_mark = "✅" if total >= 100 else "❌"
        lines.append(f"• {user}: {total} {done_mark}")

    await update.message.reply_text("\n".join(lines))

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = get_today_str()

    if today not in data or not data[today]:
        await update.message.reply_text("Сегодня ещё нет данных.")
        return

    lines = [f"📋 Подробности подходов за {today}:"]
    for user, reps_list in data[today].items():
        reps_str = ", ".join(str(x) for x in reps_list)
        lines.append(f"{user}: {reps_str}")

    await update.message.reply_text("\n".join(lines))


if __name__ == '__main__':
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    if not TOKEN:
            print("❌ Токен не найден! Проверь файл .env")
            exit()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("push", push))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("log", log))

    print("Бот запущен...")
    asyncio.run(app.run_polling())
