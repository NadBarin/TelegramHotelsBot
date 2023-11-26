from telebot.types import Message
import json
import requests
from loader import bot
from handlers.custom_handlers.universal_req import api_request


@bot.message_handler(commands=["lowprice"])
def bot_lowprice(message: Message):
    bot.reply_to(message, f"Посмотрим низкие цены! Введите город в котором хотите рассмотреть отели.")


@bot.message_handler(content_types=['text'])
def bot_city_req(message: Message):
    bot.reply_to(message, f"Обработка запроса может занять некоторое время.")
    city = message.text.strip().lower()
    querystring = {"q": "new york", "locale": "en_US", "langid": "1033", "siteid": "300000001"}
    ans = api_request('locations/v3/search', querystring, 'GET')
    string = "Вот что удалось найти:\n"
    k = 1
    for item in ans['sr']:
        if "gaiaId" in item.keys():
            payload = {
                "eapid": 1,
                "destination": {"regionId": item['gaiaId']},
                "checkInDate": {
                    "day": 10,
                    "month": 12,
                    "year": 2023
                },
                "checkOutDate": {
                    "day": 15,
                    "month": 12,
                    "year": 2023
                },
                "rooms": [
                    {
                        "adults": 2,
                        "children": [{"age": 5}, {"age": 7}]
                    }
                ],
                "resultsStartingIndex": 0,
                "resultsSize": 10,
                "sort": "PRICE_LOW_TO_HIGH",
                "filters": {
                    "price": {
                        "max": 150,
                        "min": 100
                    },
                    'availableFilter': 'SHOW_AVAILABLE_ONLY'
                }
            }
            print(payload)
            response = api_request('properties/v2/list', payload, 'POST')
            print(json.dumps(response['data']['propertySearch']['properties'][0]['name'], indent=4, sort_keys=True))
            string += f"{k}. {response['data']['propertySearch']['properties'][0]['name']}\n"
            k += 1
    bot.reply_to(message, f"{string}")
