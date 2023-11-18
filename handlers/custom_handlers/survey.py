from loader import bot
from states.questions_states import QuestionsStates
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.custom_handlers.universal_req import api_request
from loguru import logger
import json


@bot.message_handler(commands=['survey'])
def survey(message: Message) -> None:
    bot.set_state(message.from_user.id, QuestionsStates.city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город в котором будет производиться поиск отеля.')
    bot.register_next_step_handler(message.from_user.id, get_city)


@bot.message_handler(state=QuestionsStates.city)
def get_city(message: Message) -> None:
    city = message.text.strip().lower()
    if not city.isdigit():
        bot.send_message(message.from_user.id, 'Понял-понял.')
        try:
            querystring = {"q": city}
            cities = api_request('locations/v3/search', querystring, 'GET')
            if cities is None:
                raise Exception
        except:
            bot.send_message(message.from_user.id, 'Кажется есть какая то проблема.')
        else:
            keyboards_cities = InlineKeyboardMarkup()
            for item in cities['sr']:
                if "gaiaId" in item.keys():
                    keyboards_cities.add(
                        InlineKeyboardButton(text=item["regionNames"]["fullName"], callback_data=item["gaiaId"]))

            bot.send_message(message.from_user.id, 'Пожалуйста уточните местоположение.', reply_markup=keyboards_cities)
            bot.set_state(message.from_user.id, QuestionsStates.checkInDate, message.chat.id)
    else:
        bot.send_message(message.from_user.id,
                         'Название города должно содержать в себе только буквы. Попробуйте ещё раз')


@bot.callback_query_handler(func=lambda call: True)
def get_checkInDate(call):
    with bot.retrieve_data(call.from_user.id) as data:
        data["id"] = call.data
    bot.send_message(call.from_user.id, f'Понял-понял. {call.data}')
