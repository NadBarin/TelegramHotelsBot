from telebot.handler_backends import State, StatesGroup


class QuestionsStates:
    city = State()
    checkInDate = State()
    checkOutDate = State()
    adults = State()
    children = State()
    price_min = State()
    price_max = State()