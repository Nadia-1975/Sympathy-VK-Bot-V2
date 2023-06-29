import sqlalchemy as sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()


# классы пользователя, предложенных пользователей, списка избранных и списка отсеянных
class User(Base):
    __tablename__ = 'main_user'
    user_id = sql.Column(sql.Integer, primary_key=True)
    id = sql.Column(sql.Integer, unique=True)
    age = sql.Column(sql.Integer)
    city = sql.Column(sql.Integer)
    sex = sql.Column(sql.Integer)
    offset = sql.Column(sql.Integer)

    def __str__(self):
        return f'MainUser {self.id}: {self.user_id}: {self.city}: {self.age}'


class OfferedUser(Base):
    __tablename__ = 'offered_user'
    user_id = sql.Column(sql.Integer, primary_key=True)
    id = sql.Column(sql.Integer, unique=True)

    def __str__(self):
        return f'OfferedUser {self.id}: {self.user_id}: {self.city}: {self.age}'


class FavList(Base):
    __tablename__ = 'fav_list'
    user_id = sql.Column(sql.Integer, primary_key=True)
    id = sql.Column(sql.Integer, unique=True)
    first_name = sql.Column(sql.String, nullable=False)
    last_name = sql.Column(sql.String, nullable=False)
    vk_link = sql.Column(sql.String, unique=True, nullable=False)

    def __str__(self):
        return f'Favlist {self.id}: {self.user_id}, {self.first_name},' \
               f'{self.last_name}, {self.vk_link}'


class BlackList(Base):
    __tablename__ = 'black_list'
    user_id = sql.Column(sql.Integer, primary_key=True)
    id = sql.Column(sql.Integer, unique=True)

    def __str__(self):
        return f'Blacklist {self.id}: {self.user_id}'


# автоматическое создание всех таблиц
def create_tables(engine):
    Base.metadata.create_all(engine)


# очистка всех таблиц
def drop_tables(engine):
    Base.metadata.drop_all(engine)
