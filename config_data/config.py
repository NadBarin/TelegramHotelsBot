import os
from dotenv import load_dotenv, find_dotenv


if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("help", "Вывести справку"),
    ("lowprice", "Узнать топ самых дешёвых отелей в городе"),
    ("guest_rating", "Узнать топ самых популярных отелей в городе" ),
    ("bestdeal", "Узнать топ отелей, наиболее близких к центру"),
    ("history", "Узнать историю поиска отелей" )

)