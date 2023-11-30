from loader import bot
from utils.site_API.universal_req import api_request
from keyboards.inline.cities_keyboard import cities_keyboard


def request_handling(message, link, querystring, method_type):
    try:
        request = api_request(link, querystring, method_type)
        if request == 'null':
            raise Exception
        else:
            return request
    except:
        bot.send_message(message.from_user.id, 'Кажется по вашему запросу ничего не нашлось.'
                                               'Попробуйте ввести заново данные и поменять что то в процессе ввода.')
        return 0


def request_ans_handling_cities(message, city):
    querystring = {"q": city}
    cities = request_handling(message, 'locations/v3/search', querystring, 'GET')
    if cities:
        with bot.retrieve_data(message.from_user.id) as data:
            data["city"] = city
        cities_keyboard(message, cities)


def request_ans_handling_final(message, data):
    data_list = {
        "currency": "USD",
        "eapid": 1,
        "destination": {"regionId": data['gaiaId']},
        "checkInDate": {
            "day": data['checkInDate'].day,
            "month": data['checkInDate'].month,
            "year": data['checkInDate'].year
        },
        "checkOutDate": {
            "day": data['checkOutDate'].day,
            "month": data['checkOutDate'].month,
            "year": data['checkOutDate'].year,
        },
        "rooms": [
            {
                "adults": data['adults'],
                "children": data['children']
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": data['resultsSize'],
        "sort": data['sort'],
        "filters": {"price": {
            "max": data['price_max'],
            "min": data['price_min']
        }}
    }

    response = request_handling(message, 'properties/v2/list', data_list, 'POST')
    hotels_data = {}
    if response:
        for hotel in response['data']['propertySearch']['properties']:
            try:
                data_for_detales = {
                    "eapid": 1,
                    "propertyId": hotel["id"]
                }
                response_for_detales = request_handling(message, 'properties/v2/get-summary', data_for_detales, 'POST')
                if response_for_detales:
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
        return hotels_data
