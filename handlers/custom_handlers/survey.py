import datetime
from database.history import save, select, get_data
from loader import bot
from states.questions_states import QuestionsStates
from telebot.types import Message, InputMediaPhoto
from utils.site_API.request_handling import request_ans_handling_final, request_ans_handling_cities
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from random import choice


@bot.message_handler(commands=['lowprice', 'guest_rating', 'bestdeal'])
def survey(message: Message) -> None:
    '''Начало опроса. Проверяется команда и сохряняется нужный параметр сортировки поиска. Меняется состояние и
    запрашивается параметр поиска: город.'''
    bot.set_state(message.from_user.id, QuestionsStates.command)
    with bot.retrieve_data(message.from_user.id) as data:
        data.clear()
        if message.text == '/lowprice':
            data['sort'] = "PRICE_LOW_TO_HIGH"
        elif message.text == '/guest_rating':
            data['sort'] = "REVIEW"
        elif message.text == '/bestdeal':
            data['sort'] = "DISTANCE"
    bot.set_state(message.from_user.id, QuestionsStates.city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город в котором будет производиться поиск отеля.')


@bot.message_handler(state=QuestionsStates.city)
def get_city(message: Message) -> None:
    '''Совершает проверку содержит ли город числа, если нет, то пытается сделать запрос и найти все локации с таким
    названием, после чего, предоставляет пользователю выбор из найденных локаций (под сообщением появляются кнопки
    с полным названием локаций)'''
    city = message.text.strip().lower()
    if not city.isdigit():
        request_ans_handling_cities(message, city)
    else:
        bot.send_message(message.from_user.id,
                         'Название города должно содержать в себе только буквы. Попробуйте ещё раз')


@bot.callback_query_handler(func=lambda call: call.data.startswith('gaiaId.'))
def get_callback_cal_in(call):
    '''Записывает id выбранного пользователем города после нажатия пользователем соответствующей кнопки.
    Запускает календарь для планируемого заезда.'''
    bot.set_state(call.message.from_user.id, QuestionsStates.gaiaId)
    with bot.retrieve_data(call.message.chat.id) as data:
        data['gaiaId'] = call.data[7:]
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').build()
    bot.send_message(call.message.chat.id,
                     f"Теперь нужно выбрать дату планируемого заезда. Выберете год",
                     reply_markup=calendar)


def cal_out(message: Message):
    '''Запускает календарь для планируемого выезда.'''
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(message.chat.id,
                     f"Теперь нужно выбрать дату планируемого выезда. Выберете год",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal1(c):
    '''Для календаря вьезда. Проходит все этапы календаря и записывает результат в data.'''
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
        with bot.retrieve_data(c.message.chat.id) as data:
            data["checkInDate"] = result
        bot.edit_message_text(f"Вы выбрали {result} как дату вьезда.",
                              c.message.chat.id,
                              c.message.message_id)
        cal_out(c.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal2(c):
    '''Для календаря выезда. Проходит все этапы календаря и записывает результат в data.
    После этого делает запрос инфрмации про количество взрослых.'''
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
        with bot.retrieve_data(c.message.chat.id) as data:
            data["checkOutDate"] = result
        bot.edit_message_text(f"Вы выбрали {result} как дату выезда.",
                              c.message.chat.id,
                              c.message.message_id)

        bot.set_state(c.message.chat.id, QuestionsStates.adults)
        bot.send_message(c.message.chat.id, 'Введите колличество мест для взрослых.')


@bot.message_handler(state=QuestionsStates.adults)
def get_adults(message: Message) -> None:
    '''Запрашивает и записывает количество взрслых для которых нужны номера.'''
    # data["rooms"] = [{}]
    adults = message.text.strip()
    if not adults.isdigit() or int(adults) < 1:
        bot.send_message(message.from_user.id,
                         'Количество взрослых людей должно быть указанно одной цифрой > 0. Попробуйте ещё раз')
    else:
        with bot.retrieve_data(message.from_user.id) as data:
            data["adults"] = int(adults)
        # data["rooms"][0]["adults"] = int(adults)
        bot.set_state(message.from_user.id, QuestionsStates.children, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите(цифрой) на сколько детей нужны места.')


@bot.message_handler(state=QuestionsStates.children)
def get_children(message: Message) -> None:
    '''Запрашивает кличество детей и переходит к функции, которая запишет возрасты.'''
    children = message.text.strip()
    if not children.isdigit() or int(children) < 0:
        bot.send_message(message.from_user.id,
                         'Количество детей должно быть указанно одной цифрой >=0. Попробуйте ещё раз')
    else:
        if children != '0':
            # data["rooms"][0]["children"] = []
            with bot.retrieve_data(message.from_user.id) as data:
                data["children_count"] = int(children)
                data['counter'] = 1
                data["children"] = []
            bot.set_state(message.from_user.id, QuestionsStates.children_age)
            bot.send_message(message.from_user.id,
                             f'Введите возраст 1-го ребёнка.')
        else:
            bot.set_state(message.from_user.id, QuestionsStates.price_min, message.chat.id)
            bot.send_message(message.from_user.id,
                             'Хорошо. Теперь введите минимальную цену за проживание в сутки(в $).')


@bot.message_handler(state=QuestionsStates.children_age)
def get_children_age_steps(message: Message):
    "Запрашивает и записывает возрасты детей."
    age = message.text.strip()
    with bot.retrieve_data(message.from_user.id) as data:
        if age.isdigit() and int(age) >= 0:
            data["children"].append({"age": int(age)})
            if data['counter'] < data["children_count"]:
                data['counter'] += 1
                bot.send_message(message.from_user.id,
                                 f'Введите возраст {data["counter"]}-го ребёнка.')
            else:
                bot.set_state(message.from_user.id, QuestionsStates.price_min, message.chat.id)
                bot.send_message(message.from_user.id,
                                 'Хорошо. Теперь введите минимальную цену за проживание в сутки(в $).')
        else:
            bot.send_message(message.from_user.id,
                             'Возраст должен быть указан одной цифрой >= 0. Попробуйте ещё раз')


@bot.message_handler(state=QuestionsStates.price_min)
def get_price_min(message: Message) -> None:
    '''Запрашивает минимальную цену за проживание.'''
    price_min = message.text.strip()
    if not price_min.isdigit():
        bot.send_message(message.from_user.id,
                         'Цена должна быть указана цифрой. Попробуйте ещё раз.')
    else:
        with bot.retrieve_data(message.from_user.id) as data:
            data['price_min'] = int(price_min)
        bot.set_state(message.from_user.id, QuestionsStates.price_max, message.chat.id)
        bot.send_message(message.from_user.id,
                         'Хорошо. Теперь введите максимальную цену за проживание в сутки(в $).')


@bot.message_handler(state=QuestionsStates.price_max)
def get_price_max(message: Message) -> None:
    '''Запрашивает максимальную цену за проживание.'''
    price_max = message.text.strip()
    with bot.retrieve_data(message.from_user.id) as data:
        if not price_max.isdigit():
            bot.send_message(message.from_user.id,
                             'Цена должна быть указана цифрой. Попробуйте ещё раз.')
        elif data['price_min'] > int(price_max):
            bot.send_message(message.from_user.id,
                             'Максимальная цена должна быть больше минимальной. попробуйте ещё раз.')
        else:
            data["price_max"] = int(price_max)
            bot.set_state(message.from_user.id, QuestionsStates.resultsSize, message.chat.id)
            bot.send_message(message.from_user.id,
                             'Хорошо. Теперь введите максимальное количество записей, которые вывести по данному запросу.')


@bot.message_handler(state=QuestionsStates.resultsSize)
def get_results_size(message: Message):
    """Запрашивает количество результатов, которые нужно вывести. Проводит поиск нужных данных по введённым данным.
    Отправляет результат пользователю."""
    size = message.text.strip()
    if not size.isdigit():
        bot.send_message(message.from_user.id,
                         'Колличество должно быть указано цифрой. Попробуйте ещё раз.')
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["resultsSize"] = int(size)
            bot.send_message(message.from_user.id,
                             'Хорошая работа! Сейчас попробуем найти что то подходящее.')
            hotels_data = request_ans_handling_final(message, data)
            for key, post in hotels_data.items():
                bot_send_data(message, post)
            save(chat_id=message.chat.id,
                 datetime=datetime.datetime.now(),
                 city=data["city"].title(),
                 req_data=hotels_data)
    bot.delete_state(message.from_user.id, message.chat.id)


def bot_send_data(message: Message, post):
    'Формат результата, который отправляется пользователю.'
    images = post['images']
    medias = []
    for i in range(6):
        temp = choice(images)
        images.remove(temp)
        medias.append(InputMediaPhoto(media=temp))
    bot.send_media_group(message.chat.id, medias)
    bot.send_message(message.chat.id,
                     f'Название: {post["name"]}\n'
                     f'Адрес: {post["address"]}\n'
                     f'Расстояние до центра: {post["distance"]} {post["unit"].lower()}\n'
                     f'Стоимость проживания в сутки: {post["price"]} {post["currency"]}')


@bot.message_handler(commands=["history"])
def bot_history(message: Message):
    try:
        user_data = select(message)
        bot.set_state(message.from_user.id, QuestionsStates.history, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if len(user_data) > 0:
                for i in range(len(user_data)):
                    bot.send_message(message.chat.id,
                                     f"{i + 1}) Дата запроса: {user_data[i].datetime}, запрашиваемый город: "
                                     f"{user_data[i].city}")
                    data[str(i + 1)] = (user_data[i].datetime, user_data[i].city)
                bot.set_state(message.from_user.id, QuestionsStates.hist_info, message.chat.id)
                bot.send_message(message.chat.id, "Введите номер запроса чтобы вывести более подробную информацию")
            else:
                raise Exception
    except:
        bot.send_message(message.chat.id, "История пуста.")


@bot.message_handler(state=QuestionsStates.hist_info)
def get_hist_info(message: Message):
    input = message.text.strip()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if input not in data.keys():
            bot.send_message(message.chat.id, "Такого номера запоса не существует. Попробуйте ещё раз.")
        else:
            user_data = get_data(data, input)
            for key, post in user_data.req_data.items():
                bot_send_data(message, post)
    bot.delete_state(message.from_user.id, message.chat.id)
