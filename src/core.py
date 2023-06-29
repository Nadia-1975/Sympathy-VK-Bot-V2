import os
import json
import vk_api
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, InvalidRequestError, PendingRollbackError
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from vk_api.longpoll import VkLongPoll, VkEventType
from datetime import datetime

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

from database import drop_tables, create_tables, User, FavList, OfferedUser, BlackList

with open(os.path.join(__location__, './config-example.json')) as config_file:
    config_dict = json.load(config_file)

db_type = config_dict['db_params']['db_type']
db_login = config_dict['db_params']['login']
db_password = config_dict['db_params']['password']
db_hostname = config_dict['db_params']['host']
db_port = config_dict['db_params']['port']
db_name = config_dict['db_params']['database']
bot_token = config_dict['bot_params']['group_token']
user_token = config_dict['bot_params']['user_token']

base_url = f'{db_type}://{db_login}:{db_password}@{db_hostname}:{db_port}/{db_name}'
engine = create_engine(base_url)

Session_db = sessionmaker(bind=engine)
session_db = Session_db()

# создаем базу
if not database_exists(engine.url):
    print("Create DB")
    create_database(engine.url)
    # очищаем существующие таблицы
    drop_tables(engine)
    # создаем таблицы
    create_tables(engine)

vk_chatter = vk_api.VkApi(token=bot_token)
vk_searcher = vk_api.VkApi(token=user_token)
vk_bot = VkLongPoll(vk_chatter)


# механика получения данных от пользователя, который пишет боту
def get_user_info(user_id, flag=None):
    user_info = {}
    resp = vk_chatter.method('users.get',
                             {'user_id': user_id,
                              'v': 5.131,
                              'fields': 'first name, last name, bdate, sex, city'})
    if resp is not None:
        for k, v in resp[0].items():
            if k == 'city':
                if v == '':
                    if flag is None:
                        send_message(user_id, f'Введите город', None)
                        for event in vk_bot.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                user_info['city'] = city_id(event.text)[0]['id']
                                break
                else:
                    user_info[k] = v['id']
            elif k == 'bdate':
                if len(v.split('.')) != 3:
                    send_message(user_id, f'Введите дату рождения в формате "ДД.ММ.ГГГГ"', None)
                    for event in vk_bot.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            user_info['age'] = datetime.now().year - int(event.text[-4:])
                            break
                else:
                    user_info['age'] = datetime.now().year - int(v[-4:])
            else:
                user_info[k] = v

        if 'city' not in user_info.keys():
            if flag is None:
                send_message(user_id, f'Введите город', None)
                for event in vk_bot.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        user_info['city'] = city_id(event.text)[0]['id']
                        break
        user_info['offset'] = 0
        return user_info
    else:
        print('ERROR 1')
        send_message(user_info['id'], 'Ошибка 1')
        return False


def db_add_user_info(user_info):
    if user_info:
        user_db_record = session_db.query(User).filter_by(id=user_info['id']).scalar()
        if not user_db_record:
            user_db_record = User(id=user_info['id'],
                                  age=user_info['age'],
                                  city=user_info['city'],
                                  sex=user_info['sex'],
                                  offset=user_info['offset'])
        session_db.add(user_db_record)
        session_db.commit()
        print("user_info added to main_user db")
        return True
    print('ERROR 2')
    send_message(user_info['id'], 'Ошибка 2')
    return False


def db_get_user_info(user_id):
    db_user = session_db.query(User).order_by(User.user_id).all()
    if db_user:
        for item in db_user:
            if str(item.id) == user_id:
                user_info = {
                    'id': int(item.id),
                    'age': int(item.age),
                    'city': int(item.city),
                    'sex': int(item.sex),
                    'offset': int(item.offset)
                }
                return user_info
    else:
        return False


# ищем пару в соответствии с параметрами пользователя
def offered_users_search(user_info):
    post = {
        'age_from': user_info['age'] - 5,
        'age_to': user_info['age'] + 5,
        'city': user_info['city'],
        'sex': 3 - user_info['sex'],
        'relation': 6,
        'status': 1,
        'has_photo': 1,
        'count': 50,
        'v': 5.131,
        'offset': user_info['offset']
    }

    resp = vk_searcher.method('users.search', post)
    if resp and resp.get('items'):
        offered_users_list = []
        for offered_user in resp.get('items'):
            if not offered_user.get('is_closed'):
                temp = get_user_info(offered_user.get('id'),flag=True)
                if temp['age'] != 0 and temp.get('city') and temp['city'] == user_info['city']:
                    temp['vk_link'] = 'vk.com/id' + str(temp['id'])
                    offered_users_list.append(temp)
                    print('Offered user:\t', temp)
            else:
                continue
        return offered_users_list
    print('ERROR 3')
    send_message(user_info['id'], 'Ошибка 3')
    return False


def get_offered_user_photos(user_id, offer_id):
    resp = vk_searcher.method('photos.getAll', {
        'owner_id': offer_id,
        'album_id': 'profile',
        'extended': 'likes',
        'count': 25
    })
    if resp:
        if resp.get('items'):
            count = 0
            photos_list = []
            for photos in resp.get('items'):
                likes = photos.get('likes')
                photos_list.append([photos.get('owner_id'), photos.get('id'), likes.get('count')])
            sorted_photos_list = sorted(photos_list, key=lambda x: x[2], reverse=True)
            for photos in sorted_photos_list:
                photos_list.append('photo' + str(photos[0]) + '_' + str(photos[1]))
                count += 1
                if count == 3:
                    return photos_list
    print('ERROR 4')
    send_message(user_id, 'Ошибка 4')
    return False


def db_add_offered_user_info(users_data, user_id):
    try:
        users_record = session_db.query(OfferedUser).filter_by(id=users_data['id']).scalar()
        if not users_record:
            users_record = OfferedUser(id=users_data['id'])
        session_db.add(users_record)
        session_db.commit()
        return 0
    except (IntegrityError, InvalidRequestError, PendingRollbackError, TypeError):
        session_db.rollback()
        print("ERROR 5\t", "users_data:\t", users_data)
        send_message(user_id, 'Ошибка 5')
        return False


# заполняем таблицу избранного
def db_add_fav_user_info(users_data):
    user_record = session_db.query(FavList).filter_by(id=users_data['id']).scalar()
    if not user_record:
        user_record = FavList(id=users_data['id'],
                              vk_link=users_data['vk_link'],
                              first_name=users_data['first_name'],
                              last_name=users_data['last_name'])
    session_db.add(user_record)
    session_db.commit()
    return True


# заполняем таблицу отсеянных пользователей (что бы не повторялись предложения)
def db_add_blocked_user_info(users_data):
    random_user_record = session_db.query(BlackList).filter_by(id=users_data['id']).scalar()
    if not random_user_record:
        random_user_record = BlackList(id=users_data['id'])
    session_db.add(random_user_record)
    session_db.commit()
    return True


# выдаем список избранных пользователю
def db_get_fav_users_info(user_id):
    db_favorites = session_db.query(FavList).order_by(FavList.user_id).all()
    all_users = []
    if db_favorites:
        for item in db_favorites:
            all_users.append(
                [item.user_id, 'id:' + str(item.id), item.first_name + ' ' + item.last_name, item.vk_link + ' '])
        return all_users
    else:
        send_message(user_id, 'Ошибка, вы еще никого не добавили в список избранных')
        print("ERROR 6\t", "db_favorites:\t", db_favorites)
        return False


def db_get_offered_users_info():
    db_offered = session_db.query(OfferedUser).order_by(OfferedUser.user_id).all()
    all_users = []
    if db_offered:
        for item in db_offered:
            all_users.append(item.id)
        return all_users
    else:
        return []


def city_id(city_name):
    resp = vk_searcher.method('database.getCities', {
        'country_id': 1,
        'q': f'{city_name}',
        'need_all': 0,
        'count': 1000,
        'v': 5.131})
    if resp:
        if resp.get('items'):
            return resp.get('items')
        send_message(city_name, 'Ошибка ввода города')
        return False


# механика отправки сообщений пользователю
def send_message(user_id, message, attachment=None, keyboard=None):
    post = {
        "user_id": user_id,
        "message": message,
        "random_id": 0,
    }
    if keyboard is not None:
        post["keyboard"] = keyboard.get_keyboard()
    if attachment is not None:
        post["attachment"] = attachment
    else:
        post = post

    vk_chatter.method("messages.send", post)


# что бы бот продолжал писать сообщения после первого поиска (бесконечный цикл)
def loop_bot():
    for this_event in vk_bot.listen():
        if this_event.type == VkEventType.MESSAGE_NEW:
            if this_event.to_me:
                message_text = this_event.text
                return message_text
