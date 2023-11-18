from loader import bot
from states.questions_states import QuestionsStates
from telebot.types import Message


@bot.message_handler(commands=["survey"])
def survey(message: Message) -> None:
    bot.set_state(message.from_user.id, QuestionsStates.city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город в котором будет производиться поиск отеля.')

