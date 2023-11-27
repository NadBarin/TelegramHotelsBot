import peewee
from playhouse.sqlite_ext import JSONField

db = peewee.SqliteDatabase('data.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    class Meta:
        db_table = 'req_history'

    user_id = peewee.IntegerField()
    datetime = peewee.DateTimeField()
    city = peewee.CharField(max_length=100)
    req_data = JSONField()


with db:
    db.create_tables([User])
