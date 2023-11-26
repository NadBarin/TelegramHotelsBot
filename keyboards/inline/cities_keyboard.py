from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from loader import bot


def cities_keyboard(message: Message, req):
    """Кнопки для уточнения местоположения."""
    keyboards_cities = InlineKeyboardMarkup()
    for item in req['sr']:
        if "gaiaId" in item.keys():
            keyboards_cities.add(
                InlineKeyboardButton(text=item["regionNames"]["fullName"],
                                     callback_data='gaiaId.' + item["gaiaId"]))
    bot.send_message(message.from_user.id, 'Пожалуйста уточните местоположение.', reply_markup=keyboards_cities)
