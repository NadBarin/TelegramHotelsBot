from loader import bot
from states.questions_states import QuestionsStates
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.custom_handlers.universal_req import api_request
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from loguru import logger
import json

data = {"eapid": 1}


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
        bot.register_next_step_handler(message, get_city)


@bot.callback_query_handler(func=lambda call: call.data.startswith('gaiaId.'))
def get_callback(call):
    '''Записывает id выбранного пользователем города после нажатия пользователем соответствующей кнопки.'''
    data["destination"] = {}
    data["destination"]["regionId"] = call.data[6:]
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
        data["checkInDate"] = {}
        data["checkInDate"]["year"] = result.year
        data["checkInDate"]["month"] = result.month
        data["checkInDate"]["day"] = result.day
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
        data["checkOutDate"] = {}
        data["checkOutDate"]["year"] = result.year
        data["checkOutDate"]["month"] = result.month
        data["checkOutDate"]["day"] = result.day
        bot.edit_message_text(f"Вы выбрали {result} как дату выезда.",
                              c.message.chat.id,
                              c.message.message_id)
        bot.set_state(c.message.chat.id, QuestionsStates.adults)
        bot.send_message(c.message.chat.id, 'Введите колличество мест для взрослых.')


@bot.message_handler(state=QuestionsStates.adults)
def get_adults(message: Message) -> None:
    '''Запрашивает и записывает количество взрслых для которых нужны номера.'''
    data["rooms"] = [{}]
    adults = message.text.strip()
    if not adults.isdigit() or adults == '0':
        bot.send_message(message.from_user.id,
                         'Количество взрослых людей должно быть указанно одной цифрой > 0. Попробуйте ещё раз')
        bot.register_next_step_handler(message, get_adults)
    else:
        data["rooms"][0]["adults"] = int(adults)
        bot.set_state(message.from_user.id, QuestionsStates.children, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите(цифрой) на сколько детей нужны места.')


counter = 0


@bot.message_handler(state=QuestionsStates.children)
def get_children(message: Message) -> None:
    '''Запрашивает кличество детей и переходит к функции, которая запишет возрасты.'''
    children = message.text.strip()
    if not children.isdigit():
        bot.send_message(message.from_user.id,
                         'Количество детей должно быть указанно одной цифрой. Попробуйте ещё раз')
        bot.register_next_step_handler(message, get_children)
    else:
        if children != '0':
            data["rooms"][0]["children"] = []
            bot.send_message(message.from_user.id,
                             f'Введите возраст 1-го ребёнка.')
            bot.register_next_step_handler(message, get_children_age_steps, children)
        else:
            bot.set_state(message.from_user.id, QuestionsStates.currency, message.chat.id)
            bot.send_message(message.from_user.id,
                             'Хорошо. Теперь латинскими буквами введите аббревиатуру валюты, которой хотите платить '
                             'за проживание.')


counter: int = 1


def get_children_age_steps(message: Message, children: int):
    "Запрашивает и записывает возрасты детей."
    age = message.text.strip()
    if age.isdigit():
        data["rooms"][0]["children"].append({"age": int(age)})
        global counter
        if counter < int(children):
            counter += 1
            bot.send_message(message.from_user.id,
                             f'Введите возраст {counter}-го ребёнка.')
            bot.register_next_step_handler(message, get_children_age_steps, children)
        else:
            counter = 1
            bot.set_state(message.from_user.id, QuestionsStates.currency, message.chat.id)
            bot.send_message(message.from_user.id,
                             'Хорошо. Теперь латинскими буквами введите аббревиатуру валюты, которой хотите платить '
                             'за проживание.')
    else:
        bot.send_message(message.from_user.id,
                         'Возраст должен быть указан одной цифрой. Попробуйте ещё раз')
        bot.register_next_step_handler(message, get_children_age_steps, children)


@bot.message_handler(state=QuestionsStates.currency)
def get_currency(message: Message) -> None:
    '''Запрашивает валюту.'''
    currency = message.text.strip().upper()
    if len(currency) > 3 or not currency.isalpha():
        bot.send_message(message.from_user.id,
                         'Валюта должна быть указана тремя латинскими буквами. Попробуйте ещё раз.')
        bot.register_next_step_handler(message, get_currency)
    else:
        data["currency"] = currency
        bot.set_state(message.from_user.id, QuestionsStates.price_min, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите минимальную цену за проживание.')


@bot.message_handler(state=QuestionsStates.price_min)
def get_price_min(message: Message) -> None:
    '''Запрашивает минимальную цену за проживание.'''
    price_min = message.text.strip()
    if not price_min.isdigit():
        bot.send_message(message.from_user.id,
                         'Цена должна быть указана цифрой. Попробуйте ещё раз.')
        bot.register_next_step_handler(message, get_price_min)
    else:
        data["filters"] = {}
        data["filters"]["price"] = {}
        data["filters"]["price"]["min"] = int(price_min)
        bot.set_state(message.from_user.id, QuestionsStates.price_max, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите максимальную цену за проживание.')


@bot.message_handler(state=QuestionsStates.price_max)
def get_price_max(message: Message) -> None:
    '''Запрашивает минимальную цену за проживание.'''
    price_max = message.text.strip()
    if not price_max.isdigit():
        bot.send_message(message.from_user.id,
                         'Цена должна быть указана цифрой. Попробуйте ещё раз.')
        bot.register_next_step_handler(message, get_price_max)
    elif data["filters"]["price"]["min"] > int(price_max):
        bot.send_message(message.from_user.id,
                         'Максимальная цена должна быть больше минимальной. попробуйте ещё раз.')
        bot.register_next_step_handler(message, get_price_max)
    else:
        data["filters"]["price"]["max"] = int(price_max)
        data["filters"]["availableFilter"] = 'SHOW_AVAILABLE_ONLY'
        bot.set_state(message.from_user.id, QuestionsStates.resultsSize, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите количество записей, которые вывести по данному запросу.')


@bot.message_handler(state=QuestionsStates.resultsSize)
def get_results_size(message: Message):
    "Запрашивает количество результатов, которые нужно вывести."
    size = message.text.strip()
    if not size.isdigit():
        bot.send_message(message.from_user.id,
                         'Колличество должно быть указано цифрой. Попробуйте ещё раз.')
        bot.register_next_step_handler(message, get_results_size)
    else:
        data["resultsStartingIndex"] = 0
        data["resultsSize"] = int(size)
        bot.send_message(message.from_user.id,
                         'Хорошая работа! Сейчас попробуем найти что то подхдящее.')
        print(data)
