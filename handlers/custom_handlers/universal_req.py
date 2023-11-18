from requests import get, codes, post

headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": "6ebe2836f8msh38e1f5542c2aef7p18d486jsndac0197ed05d",
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
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
        if response.status_code == codes.ok:
            return response.json()
    except:
        return "Ошибка"


def post_request(url, params):
    try:
        response = post(
            url,
            headers=headers,
            json=params,
            timeout=15
        )
        if response.status_code == codes.ok:
            return response.json()
    except:
        return "Ошибка"
