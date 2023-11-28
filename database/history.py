import peewee
from playhouse.sqlite_ext import JSONField

db = peewee.SqliteDatabase('data.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    class Meta:
        db_table = 'req_history'

    chat_id = peewee.IntegerField()
    datetime = peewee.DateTimeField()
    city = peewee.CharField(max_length=100)
    req_data = JSONField()


with db:
    db.create_tables([User])


def save(chat_id, datetime, city, req_data):
    User(chat_id=chat_id, datetime=datetime, city=city, req_data=req_data).save()


def select(message):
    return [x for x in User.select().where(User.chat_id == message.chat.id)]


def get_data(user_data_dict, input):
    return User.get(datetime=user_data_dict[input][0], city=user_data_dict[input][1])
