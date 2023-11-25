import datetime
import peewee
from database.history import User
from loader import bot
from states.questions_states import QuestionsStates
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from handlers.custom_handlers.universal_req import api_request
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from random import choice
import json

data = {"eapid": 1}
citydb = ''


@bot.message_handler(commands=['lowprice', 'guest_rating', 'bestdeal'])
def survey(message: Message) -> None:
    '''Начало опроса. Проверяется команда и сохряняется нужный параметр сортировки поиска. Меняется состояние и
    запрашивается параметр поиска: город.'''
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
        bot.send_message(message.from_user.id, 'Понял-понял.')
        try:
            querystring = {"q": city}
            cities = api_request('locations/v3/search', querystring, 'GET')
            if cities == 'null':
                raise Exception
        except:
            bot.send_message(message.from_user.id, 'Кажется мы не нашли такого города, попробуйте ещё раз.')
            bot.register_next_step_handler(message, get_city)
        else:
            global citydb
            citydb = city
            keyboards_cities = InlineKeyboardMarkup()
            for item in cities['sr']:
                if "gaiaId" in item.keys():
                    keyboards_cities.add(
                        InlineKeyboardButton(text=item["regionNames"]["fullName"],
                                             callback_data='gaiaId.' + item["gaiaId"]))
            bot.send_message(message.from_user.id, 'Пожалуйста уточните местоположение.', reply_markup=keyboards_cities)
    else:
        bot.send_message(message.from_user.id,
                         'Название города должно содержать в себе только буквы. Попробуйте ещё раз')
        bot.register_next_step_handler(message, get_city)


@bot.callback_query_handler(func=lambda call: call.data.startswith('gaiaId.'))
def get_callback_cal_in(call):
    '''Записывает id выбранного пользователем города после нажатия пользователем соответствующей кнопки.
    Запускает календарь для планируемого заезда.'''
    data["destination"] = {}
    data["destination"]["regionId"] = call.data[7:]
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
    '''Проходит все этапы календаря и записывает результат в data.'''
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
        cal_out(c.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal2(c):
    '''Проходит все этапы календаря и записывает результат в data. После этого делает запрос инфрмации про
    количество взрослых.'''
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
    if not adults.isdigit() or int(adults) < 1:
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
    if not children.isdigit() or int(children) < 0:
        bot.send_message(message.from_user.id,
                         'Количество детей должно быть указанно одной цифрой >=0. Попробуйте ещё раз')
        bot.register_next_step_handler(message, get_children)
    else:
        if children != '0':
            data["rooms"][0]["children"] = []
            bot.send_message(message.from_user.id,
                             f'Введите возраст 1-го ребёнка.')
            bot.register_next_step_handler(message, get_children_age_steps, children)
        else:
            bot.set_state(message.from_user.id, QuestionsStates.price_min, message.chat.id)
            bot.send_message(message.from_user.id,
                             'Хорошо. Теперь введите минимальную цену за проживание в сутки(в $).')


counter: int = 1


def get_children_age_steps(message: Message, children: int):
    "Запрашивает и записывает возрасты детей."
    age = message.text.strip()
    if age.isdigit() and int(age) >= 0:
        data["rooms"][0]["children"].append({"age": int(age)})
        global counter
        if counter < int(children):
            counter += 1
            bot.send_message(message.from_user.id,
                             f'Введите возраст {counter}-го ребёнка.')
            bot.register_next_step_handler(message, get_children_age_steps, children)
        else:
            counter = 1
            bot.set_state(message.from_user.id, QuestionsStates.price_min, message.chat.id)
            bot.send_message(message.from_user.id,
                             'Хорошо. Теперь введите минимальную цену за проживание в сутки(в $).')
    else:
        bot.send_message(message.from_user.id,
                         'Возраст должен быть указан одной цифрой >= 0. Попробуйте ещё раз')
        bot.register_next_step_handler(message, get_children_age_steps, children)


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
                         'Хорошо. Теперь введите максимальную цену за проживание в сутки(в $).')


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
                         'Хорошо. Теперь введите максимальное количество записей, которые вывести по данному запросу.')


@bot.message_handler(state=QuestionsStates.resultsSize)
def get_results_size(message: Message):
    """Запрашивает количество результатов, которые нужно вывести. Проводит поиск нужных данных по введённым данным. Отправляет результат пользователю."""
    size = message.text.strip()
    if not size.isdigit():
        bot.send_message(message.from_user.id,
                         'Колличество должно быть указано цифрой. Попробуйте ещё раз.')
        bot.register_next_step_handler(message, get_results_size)
    else:
        data["resultsStartingIndex"] = 0
        data["resultsSize"] = int(size)
        bot.send_message(message.from_user.id,
                         'Хорошая работа! Сейчас попробуем найти что то подходящее.')
        response = api_request('properties/v2/list', data, 'POST')
        with open("file.txt", "w", encoding='UTF-8') as file:
            json.dump(response, file, indent=4, sort_keys=True)
        hotels_data = {}
        if response == 'null':
            bot.send_message(message.from_user.id,
                             'Кажется по вашему запросу ничего не нашлось. '
                             'Попробуйте ввести заново данные и поменять что то в процессе ввода.')
        else:
            for hotel in response['data']['propertySearch']['properties']:
                try:
                    data_for_detales = {
                        "eapid": 1,
                        "propertyId": hotel["id"]
                    }
                    response_for_detales = api_request('properties/v2/get-summary', data_for_detales, 'POST')
                    # print(json.dumps(response_for_detales["data"]["propertyInfo"], indent=4, sort_keys=True))
                    with open("file2.txt", "w", encoding='UTF-8') as file2:
                        json.dump(response_for_detales, file2, indent=4, sort_keys=True)
                    hotels_data[hotel["id"]] = {
                        'name': hotel["name"],
                        'id': hotel["id"],
                        'address': response_for_detales["data"]["propertyInfo"]["summary"]["location"]["address"][
                            "addressLine"],
                        'distance': hotel["destinationInfo"]["distanceFromDestination"]["value"],
                        'unit': hotel["destinationInfo"]["distanceFromDestination"]["unit"],
                        'price': round(hotel['price']['lead']['amount'], 2),
                        'currency': hotel['price']['lead']["currencyInfo"]["code"],
                        'images': [url["image"]["url"] for url in
                                   response_for_detales['data']['propertyInfo']["propertyGallery"]["images"]]
                    }
                except (TypeError, KeyError):
                    continue
            for key, post in hotels_data.items():
                bot_send_data(message, post)
            User(user_id=message.chat.id,
                 datetime=datetime.datetime.now(),
                 city=citydb,
                 req_data=hotels_data).save()
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
    new_dict = dict()
    try:
        user_data = [x for x in User.select().where(User.user_id == message.chat.id)]
        if len(user_data) > 0:
            for i in range(len(user_data)):
                bot.send_message(message.chat.id,
                                 f"{i + 1}) Дата запроса: {user_data[i].datetime}, запрашиваемый город: "
                                 f"{user_data[i].city}")
                new_dict[str(i + 1)] = (user_data[i].datetime, user_data[i].city)
            bot.send_message(message.chat.id, "Введите номер запроса чтобы вывести более подробную информацию")
            bot.register_next_step_handler(message, get_hist_info, new_dict)
        else:
            raise Exception
    except:
        bot.send_message(message.chat.id, "История пуста.")


def get_hist_info(message: Message, user_data_dict):
    input = message.text.strip()
    if input not in user_data_dict.keys():
        bot.send_message(message.chat.id, "Такого номера запоса не существует. Попробуйте ещё раз.")
        bot.register_next_step_handler(message, get_hist_info, user_data_dict)
    else:
        user_data = User.get(datetime=user_data_dict[input][0], city=user_data_dict[input][1])
        req_data = eval(user_data.req_data)
        for key, post in req_data.items():
            bot_send_data(message, post)
