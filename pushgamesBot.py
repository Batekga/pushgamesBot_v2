import logging
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DATA_FILE = 'pushup_data.json'
GOAL_FILE = 'goals.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_goals():
    if os.path.exists(GOAL_FILE):
        with open(GOAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_goals(goals):
    with open(GOAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)

def get_today_str():
    return datetime.now().strftime('%Y-%m-%d')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для учёта отжиманий.\n"
        "Команды:\n"
        "/push <число> — добавить подход\n"
        "/stats — статистика за сегодня\n"
        "/log — подробности подходов\n"
        "/setgoal <число> — установить цель"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/push <число> — добавить подход с повторениями\n"
        "/stats — текущий прогресс\n"
        "/log — подробности подходов\n"
        "/setgoal <число> — установить цель"
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
    goals = load_goals()
    today = get_today_str()

    if today not in data or not data[today]:
        await update.message.reply_text("Сегодня ещё нет данных.")
        return

    lines = [f"📊 Статистика за {today}:"]
    for user, reps_list in data[today].items():
        total = sum(reps_list)
        user_goal = goals.get(today, {}).get(user)
        if user_goal:
            done_mark = "✅" if total >= user_goal else "❌"
            lines.append(f"• {user}: {total}/{user_goal} {done_mark}")
        else:
            done_mark = "✅" if total >= 100 else "❌"
            lines.append(f"• {user}: {total} {done_mark} (цель по умолчанию: 100)")

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

async def setgoal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.first_name or user.username or "Аноним"
    args = context.args

    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("Укажи цель числом, например:\n/setgoal 100")
        return

    goal = int(args[0])
    if goal <= 0:
        await update.message.reply_text("Цель должна быть положительным числом.")
        return

    goals = load_goals()
    today = get_today_str()

    if today not in goals:
        goals[today] = {}

    goals[today][username] = goal
    save_goals(goals)

    await update.message.reply_text(f"🎯 Цель на сегодня установлена: {goal} отжиманий.")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("push", push))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("log", log))
    app.add_handler(CommandHandler("setgoal", setgoal))

    print("Бот запущен...")
    asyncio.run(app.run_polling())
