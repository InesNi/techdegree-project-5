from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *
from datetime import date


DATABASE = SqliteDatabase('journal.db', pragmas={'foreign_keys': 1})


class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, username, email, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password))
        except IntegrityError:
            raise ValueError("User already exists")


class Entry(Model):
    title = CharField()
    date = DateField(default=date.today)
    time_spent = IntegerField()
    content = TextField()
    resources = TextField()
    slug = CharField(unique=True)
    author = ForeignKeyField(User, related_name='entries')

    class Meta:
        database = DATABASE
        order_by = ('-date',)

    def get_tags(self):
        return (
            Tag.select().join(
                EntryTags, on=EntryTags.tag
            ).where(
                EntryTags.entry == self
            )
        )


class Tag(Model):
    tag = CharField(unique=True)

    class Meta:
        database = DATABASE

    def get_entries(self):
        return (
            Entry.select().join(
                EntryTags, on=EntryTags.entry
            ).where(
                EntryTags.tag == self
            )
        )
    
    def __str__(self):
        return str(self.tag)


class EntryTags(Model):
    entry = ForeignKeyField(Entry, related_name='for_entry')
    tag = ForeignKeyField(Tag, related_name='for_tag')

    class Meta:
        database = DATABASE
        indexes = (
            (('entry', 'tag'), True),
        )


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Entry, Tag, EntryTags], safe=True)
    DATABASE.close()
