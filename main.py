from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import BadRequest
from apscheduler.schedulers.background import BackgroundScheduler
import random
import json
from datetime import datetime
import pytz

DATA_FILE = 'pidor_stats.json'

def load_stats():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    with open(DATA_FILE, 'w') as f:
        json.dump(stats, f)

async def choose_pidor(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.context
    try:
        members = await context.bot.get_chat_administrators(chat_id)
        chat_members = [admin.user for admin in members if not admin.user.is_bot]
        if not chat_members:
            return

        pidor = random.choice(chat_members)
        stats = load_stats()
        user_id = str(pidor.id)
        stats[user_id] = stats.get(user_id, 0) + 1
        save_stats(stats)

        await context.bot.send_message(chat_id, f'Сегодня пидор — @{pidor.username or pidor.first_name}')
    except BadRequest as e:
        print(f"Ошибка: {e}")

async def pidorstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    stats = load_stats()
    if not stats:
        await update.message.reply_text("Статистика пуста.")
        return

    result = "🏆 Статистика пидоров:
"
    for user_id, count in stats.items():
        try:
            user = await context.bot.get_chat_member(chat_id, int(user_id))
            result += f"{user.user.first_name}: {count}
"
        except Exception:
            continue

    await update.message.reply_text(result)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    scheduler.add_job(choose_pidor, 'cron', hour=12, minute=0, timezone=pytz.timezone('Europe/Moscow'), args=[context], context=chat_id)
    await update.message.reply_text("Бот запущен и будет выбирать пидора каждый день в 12:00 по МСК.")

if __name__ == '__main__':
    from telegram.ext import Application

    TOKEN = 'ТВОЙ_ТОКЕН_БОТА'

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pidorstats", pidorstats))

    scheduler = BackgroundScheduler()
    scheduler.start()

    app.run_polling()
