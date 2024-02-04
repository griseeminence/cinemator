import logging
from dotenv import dotenv_values
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Загрузить переменные среды из файла .env
env_variables = dotenv_values(".env")

# Получить значение конкретной переменной
token = env_variables.get("TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()