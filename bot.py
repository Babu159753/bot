import logging
import os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, CallbackContext, JobQueue
)
from schedule_data import SCHEDULE

# Включаем логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения групп пользователей
user_groups = {}

# Кнопки команд
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Today", callback_data='today')],
        [InlineKeyboardButton("📆 Tomorrow", callback_data='tomorrow')],
        [InlineKeyboardButton("🗓️ Week", callback_data='week')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Кнопки выбора группы
def get_group_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(group, callback_data=f'setgroup:{group}')]
        for group in SCHEDULE.keys()
    ])

# Формат расписания
def format_schedule(day_data):
    if not day_data:
        return "No classes 📭"
    return '\n'.join([
        f"⏰ {cls['time']} | 📘 {cls['course']} | 🏫 {cls.get('location', '')}"
        for cls in day_data
    ])

# Получить расписание на определённый день
def get_day_schedule(group, date):
    weekday = date.strftime('%A')
    return SCHEDULE.get(group, {}).get(weekday, [])

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_groups:
        await update.message.reply_text("Please select your group 👇", reply_markup=get_group_keyboard())
    else:
        await update.message.reply_text("Choose a command 👇", reply_markup=get_main_keyboard())

# Обработка кнопок
async def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data.startswith('setgroup:'):
        group = query.data.split(':')[1]
        user_groups[user_id] = group
        await query.edit_message_text(f"Group set to {group} ✅", reply_markup=get_main_keyboard())

    elif user_id not in user_groups:
        await query.edit_message_text("Please select your group first 👇", reply_markup=get_group_keyboard())

    else:
        group = user_groups[user_id]
        if query.data == 'today':
            text = format_schedule(get_day_schedule(group, datetime.now()))
            await query.edit_message_text(f"📅 Today’s Schedule:\n\n{text}")
        elif query.data == 'tomorrow':
            text = format_schedule(get_day_schedule(group, datetime.now() + timedelta(days=1)))
            await query.edit_message_text(f"📆 Tomorrow’s Schedule:\n\n{text}")
        elif query.data == 'week':
            message = f"🗓️ Weekly Schedule for {group}:\n\n"
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                schedule = SCHEDULE[group].get(day, [])
                message += f"📌 {day}:\n{format_schedule(schedule)}\n\n"
            await query.edit_message_text(message)
        elif query.data == 'settings':
            await query.edit_message_text("Select your group 👇", reply_markup=get_group_keyboard())

# Ежедневное отправление расписания
async def send_daily_schedule(context: CallbackContext):
    now = datetime.now()
    for user_id, group in user_groups.items():
        today_schedule = format_schedule(get_day_schedule(group, now))
        await context.bot.send_message(chat_id=user_id, text=f"📅 Good morning! Here is your schedule for today:\n\n{today_schedule}")

# Главный запуск
async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    # Планировщик на 6:00 утра
    app.job_queue.run_daily(send_daily_schedule, time=datetime.strptime("06:00", "%H:%M").time())

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
