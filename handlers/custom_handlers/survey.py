from loader import bot
from states.questions_states import QuestionsStates
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.custom_handlers.universal_req import api_request
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from loguru import logger
import json

data = dict()


@bot.message_handler(commands=['survey'])
def survey(message: Message) -> None:
    '''Начало опроса. меняется состояние и запрашивается первый параметр поиска: город.'''
    bot.set_state(message.from_user.id, QuestionsStates.city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город в котором будет производиться поиск отеля.')


@bot.message_handler(state=QuestionsStates.city)
def get_city(message: Message) -> None:
    '''Совершает проверку содержит ли город числа, если нет, то пытается сделать запрос и найти все локации с таким
    названием, после чего, предоставляет пользователю выбор из найденных локаций (под сообщением появляются кнопки
    с полным названием локаций)'''
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
                        InlineKeyboardButton(text=item["regionNames"]["fullName"],
                                             callback_data='gaiaId.' + item["gaiaId"]))

            bot.send_message(message.from_user.id, 'Пожалуйста уточните местоположение.', reply_markup=keyboards_cities)
            bot.set_state(message.from_user.id, QuestionsStates.checkInDate, message.chat.id)
    else:
        bot.send_message(message.from_user.id,
                         'Название города должно содержать в себе только буквы. Попробуйте ещё раз')


@bot.callback_query_handler(func=lambda call: call.data.startswith('gaiaId.'))
def get_callback(call):
    '''Записывает id выбранного пользователем города после нажатия пользователем соответствующей кнопки.'''
    data["id"] = call.data[6:]
    bot.send_message(call.from_user.id, f'Понял-понял. {data["id"]}')


@bot.message_handler(commands=['start1'])
def start1(message: Message):
    '''Запускает календарь для планируемого заезда.'''
    # do not forget to put calendar_id
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').build()
    bot.send_message(message.chat.id,
                     f"Теперь нужно выбрать дату планируемого заезда. Выберете год",
                     reply_markup=calendar)


def start2(message: Message):
    '''Запускает календарь для планируемого выезда.'''
    # do not forget to put calendar_id
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(message.chat.id,
                     f"Теперь нужно выбрать дату планируемого выезда. Выберете год",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal1(c):
    '''Проходит все этапы календаря и записывает результат в data.'''
    # calendar_id is used here too, since the new keyboard is made
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').process(c.data)
    if not result and key:
        if LSTEP[step] == 'month':
            bot.edit_message_text(f"Выберете месяц",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif LSTEP[step] == 'day':
            bot.edit_message_text(f"Выберете день",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
    elif result:
        data["checkInDate"] = result
        bot.edit_message_text(f"Вы выбрали {result} как дату вьезда.",
                              c.message.chat.id,
                              c.message.message_id)
        start2(c.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal1(c):
    '''Проходит все этапы календаря и записывает результат в data. После этого делает запрос инфрмации про
    количество взрослых.'''
    # calendar_id is used here too, since the new keyboard is made
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(c.data)
    if not result and key:
        if LSTEP[step] == 'month':
            bot.edit_message_text(f"Выберете месяц",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif LSTEP[step] == 'day':
            bot.edit_message_text(f"Выберете день",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
    elif result:
        data["checkOutDate"] = result
        bot.edit_message_text(f"Вы выбрали {result} как дату выезда.",
                              c.message.chat.id,
                              c.message.message_id)
        bot.set_state(c.message.chat.id, QuestionsStates.adults)
        bot.send_message(c.message.chat.id, 'Введите колличество мест для взрослых.')


@bot.message_handler(state=QuestionsStates.adults)
def get_adults(message: Message) -> None:
    adults = message.text.strip()
    if not adults.isdigit():
        bot.send_message(message.from_user.id,
                         'Количество взрослых людей должно быть указанно одной цифрой. Попробуйте ещё раз')
    else:
        data["adults"] = int(adults)
        print(data)
        bot.set_state(message.from_user.id, QuestionsStates.children, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите(цифрой) на сколько детей нужны места.')


'''  
@bot.message_handler(state=QuestionsStates.children)
def get_children(message: Message) -> None:
    children = message.text.strip()
    if not children.isdigit():
        bot.send_message(message.from_user.id,
                         'Количество детей должно быть указанно одной цифрой. Попробуйте ещё раз')
    else:
        data["children"] = int(children)
        bot.set_state(message.from_user.id, QuestionsStates.children, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите(цифрой) на сколько детей нужны места.')
'''
