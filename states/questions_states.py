from telebot.handler_backends import State, StatesGroup


class QuestionsStates(StatesGroup):
    city = State()
    checkDate = State()
    adults = State()
    children = State()
    currency = State
    price_min = State()
    price_max = State()
    resultsSize = State()

