import os
import json
import random

import vk_api
from sqlalchemy.exc import IntegrityError, InvalidRequestError, PendingRollbackError
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from database import *
from datetime import datetime

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
with open(os.path.join(__location__, './config.json')) as config_file:
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
    create_database(engine.url)

# очищаем существующие таблицы
drop_tables(engine)
# создаем таблицы
create_tables(engine)

vk_chatter = vk_api.VkApi(token=bot_token)
vk_searcher = vk_api.VkApi(token=user_token)
vk_bot = VkLongPoll(vk_chatter)


# механика получения данных от пользователя, который пишет боту
def get_user_info(user_id):
    user_info = {}
    resp = vk_chatter.method('users.get',
                             {'user_id': user_id,
                              'v': 5.131,
                              'fields': 'first name, last name, bdate, sex, city'})
    if resp is not None:
        for k, v in resp[0].items():
            if k == 'city':
                user_info[k] = v['id']
            elif k == 'bdate':
                if len(v.split('.')) != 3:
                    user_info['age'] = 0
                else:
                    user_info['age'] = datetime.now().year - int(v[-4:])
            else:
                user_info[k] = v
                user_info['city'] = 125
        return user_info
    else:
        send_message(user_info['id'], 'Ошибка 1')
        return 1


def db_add_user_info(user_info):
    if user_info:
        user_db_record = session_db.query(User).filter_by(id=user_info['id']).scalar()
        if not user_db_record:
            user_db_record = User(id=user_info['id'],
                                  first_name=user_info['first_name'],
                                  last_name=user_info['last_name'],
                                  age=user_info['age'],
                                  sex=user_info['sex'],
                                  city=user_info['city'])
        session_db.add(user_db_record)
        session_db.commit()
        return 0
    send_message(user_info['id'], 'Ошибка 2')
    return 1


# ищем пару в соответствии с параметрами пользователя
def offered_users_search(user_info):
    resp = vk_searcher.method('users.search', {
        'age_from': user_info['age'] - 5,
        'age_to': user_info['age'] + 5,
        'city': user_info['city'],
        'sex': 3 - user_info['sex'],
        'relation': 6,
        'status': 1,
        'has_photo': 1,
        'count': 50,
        'v': 5.131})
    if resp and resp.get('items'):
        offered_users_list = []
        for offered_user in resp.get('items'):
            if offered_user.get('is_closed') != True:
                temp = get_user_info(offered_user.get('id'))
                if temp['age'] != 0 and 'city' in temp and temp['city'] == user_info['city']:
                    temp['vk_link'] = 'vk.com/id' + str(temp['id'])
                    offered_users_list.append(temp)
                    print(temp)
            else:
                continue
        return offered_users_list
    send_message(user_info['id'], 'Ошибка 3')
    return 1


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
    send_message(user_id, 'Ошибка 4')
    return 1


# выбираем случайный аккаунт из полученного списка
def get_random_user(users_data, user_id):
    if users_data:
        return random.choice(users_data)
    send_message(user_id, 'Ошибка')
    return False


def db_add_offered_user_info(users_data, user_id):
    try:
        users_record = session_db.query(OfferedUser).filter_by(id=users_data['id']).scalar()
        if not users_record:
            users_record = OfferedUser(id=users_data['id'],
                                       first_name=users_data['first_name'],
                                       last_name=users_data['last_name'],
                                       age=users_data['age'],
                                       sex=users_data['sex'],
                                       city=users_data['city'],
                                       offered_to_user_id=user_id)
        session_db.add(users_record)
        session_db.commit()
        return 0
    except (IntegrityError, InvalidRequestError, PendingRollbackError, TypeError):
        session_db.rollback()
        print("ERROR 5")
        print(users_data)
        send_message(user_id, 'Ошибка 5')
        return 1


# заполняем таблицу избранного
def db_add_fav_user_info(users_data):
    print("\n\n\nFAV\n\n\n", users_data)
    random_user_record = session_db.query(FavList).filter_by(id=users_data['id']).scalar()
    if not random_user_record:
        random_user_record = FavList(id=users_data['id'],
                                     first_name=users_data['first_name'],
                                     last_name=users_data['last_name'],
                                     vk_link=users_data['vk_link'],
                                     age=users_data['age'],
                                     sex=users_data['sex'],
                                     city=users_data['city']
                                     )
    session_db.add(random_user_record)
    session_db.commit()
    return 0


# заполняем таблицу отсеянных пользователей (что бы не повторялись предложения)
def db_add_blocked_user_info(users_data):
    random_user_record = session_db.query(BlackList).filter_by(id=users_data['id']).scalar()
    if not random_user_record:
        random_user_record = BlackList(id=users_data['id'])
    session_db.add(random_user_record)
    session_db.commit()
    return 0


# выдаем список избранных пользователю
def db_get_fav_users_info(user_id):
    db_favorites = session_db.query(FavList).order_by(FavList.user_id).all()
    all_users = []
    if db_favorites:
        for item in db_favorites:
            print(item)
            all_users.append([item.user_id, 'id:' + str(item.id), item.first_name + ' ' + item.last_name, item.vk_link + ' '])
        return all_users
    else:
        send_message(user_id, 'Ошибка, вы еще никого не добавили в список избранных')
        print("ERROR 6")
        print(db_favorites)
    return 1


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
