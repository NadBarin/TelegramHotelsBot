from requests import get, post
from config_data.config import RAPID_API_KEY, RAPID_API_HOST

headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": RAPID_API_HOST
}


def api_request(method_endswith,  # Меняется в зависимости от запроса. locations/v3/search либо properties/v2/list
                params,  # Параметры, если locations/v3/search, то {'q': 'Рига', 'locale': 'ru_RU'}
                method_type  # Метод\тип запроса GET\POST
                ):
    url = f"https://hotels4.p.rapidapi.com/{method_endswith}"

    # В зависимости от типа запроса вызываем соответствующую функцию
    if method_type == 'GET':
        return get_request(
            url=url,
            params=params
        )
    else:
        return post_request(
            url=url,
            params=params
        )


def get_request(url, params):
    try:
        response = get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception
    except:
        return "null"


def post_request(url, params):
    try:
        response = post(
            url,
            headers=headers,
            json=params,
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception
    except:
        return "null"
