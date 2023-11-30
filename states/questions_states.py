from telebot.handler_backends import State, StatesGroup


class QuestionsStates(StatesGroup):
    command = State()
    city = State()
    gaiaId = State()
    checkDate = State()
    adults = State()
    children = State()
    children_age = State()
    price_min = State()
    price_max = State()
    resultsSize = State()
    history = State()
    hist_info = State()

