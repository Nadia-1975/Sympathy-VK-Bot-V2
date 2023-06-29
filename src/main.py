from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType
from core import vk_bot, db_get_user_info, get_user_info, db_add_user_info, send_message, offered_users_search, \
    db_get_offered_users_info, get_offered_user_photos, db_add_offered_user_info, loop_bot, db_add_fav_user_info, \
    db_add_blocked_user_info, db_get_fav_users_info


def main():
    user_info = []
    viewed_list = []
    offered_list = []

    for event in vk_bot.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = str(event.user_id)
            print("user_id:\t", user_id)
            if not user_info:
                user_info = db_get_user_info(user_id)
                print("user_info from DB:\t", user_info)
            request = event.text.lower()
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button(label='Избранное', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button(label='Да', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button(label='Нет', color=VkKeyboardColor.NEGATIVE)

            if request == 'привет':
                if not user_info:
                    user_info = get_user_info(user_id)
                    db_add_user_info(user_info)
                send_message(user_id, 'Приветствую! \n ' +
                             'Я SympathyBot! \n ' +
                             'Я осуществляю поиск людей противоположного пола из твоего города \n' +
                             'Так же я могу добавить понравившихся тебе людей в список избранных, ' +
                             'а потом показать их тебе \n' +
                             'Ну что, начнем поиски ?', keyboard=keyboard)

            elif request in ["да"]:
                if not offered_list:
                    send_message(user_id, "Ищу подходящих кандидатов... Пожалуйста подождите...")
                    offered_list = offered_users_search(user_info)
                    print("offered_users_info from VK:\t", offered_list)
                if not viewed_list:
                    viewed_list = db_get_offered_users_info()
                    print("viewed_list:\t", viewed_list)

                send_message(user_id, f"Найдено {len(offered_list)} кандидатов")
                for user in offered_list:
                    if user['id'] not in viewed_list:
                        send_message(user_id,
                                     message={user['first_name'] + ' ' + user['last_name']},
                                     attachment=get_offered_user_photos(user_id, user['id']))
                        send_message(user_id, f"Ссылка на профиль: {user['vk_link']}")
                        send_message(user_id, "Занести пользователя в список избранных?", keyboard=keyboard)
                        db_add_offered_user_info(user, user_id)
                        message_text = loop_bot()
                        if message_text == 'Да':
                            db_add_fav_user_info(user)
                            viewed_list.append(user['id'])
                            send_message(user_id, "Кандидат занесен в список избранных")
                            print("ADDED to FavList:\t", user)
                        elif message_text == 'Нет':
                            db_add_blocked_user_info(user)
                            viewed_list.append(user['id'])
                            send_message(user_id, "Кандидат занесен в черный список")
                            print("ADDED to Blacklist:\t", user)
                        elif message_text == 'Избранное':
                            send_message(user_id, f"{db_get_fav_users_info(user_id)}")

                        send_message(user_id, "Продолжим ?", keyboard=keyboard)
                        message_text = loop_bot()
                        if message_text == 'Да':
                            continue
                        elif message_text == 'Нет':
                            send_message(user_id, 'Что ж, тогда в следующий раз, пока :)')
                            break
                        elif message_text == 'Избранное':
                            send_message(user_id, f"{db_get_fav_users_info(user_id)}")
                    else:
                        continue

                user_info['offset'] += 50
                if user_info['offset'] >= 1000:
                    user_info['offset'] = 0
                db_add_user_info(user_info)
                offered_list = []
                send_message(user_id, "Продолжим ?", keyboard=keyboard)


            elif request == 'избранное':
                send_message(user_id, f"{db_get_fav_users_info(user_id)}")
                send_message(user_id, "Продолжим ?", keyboard=keyboard)

            elif request == 'нет':
                send_message(user_id, 'Что ж, тогда в следующий раз, пока :)')
                break
            else:
                send_message(user_id, 'Для начала работы введите "привет"')


main()
