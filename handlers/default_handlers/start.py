from telebot.types import Message
from loader import bot


@bot.message_handler(commands=["start"])
def bot_start(message: Message):
    bot.send_message(message.from_user.id, f"Привет, {message.from_user.full_name}! Я бот поиска отелей по заданным "
                                           f"параметрам. Введите /help чтобы узнать больше о моих взможностях.")
