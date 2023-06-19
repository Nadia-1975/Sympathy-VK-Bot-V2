from core import *


def main():
    if not database_exists(engine.url):
        create_database(engine.url)
    create_tables(engine)
    list_chosen = []
    random_user = []
    for event in vk_bot.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = str(event.user_id)
            request = event.text.lower()
            user_info = get_user_info(user_id)
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button(label='Избранное', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button(label='Да', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button(label='Нет', color=VkKeyboardColor.NEGATIVE)

            if request == 'привет':
                db_add_user_info(user_info)
                send_message(user_id, 'Приветствую! \n ' +
                             'Я SympathyBot! \n ' +
                             'Я осуществляю поиск людей противоположного пола из твоего города \n' +
                             'Так же я могу добавить понравившихся тебе людей в список избранных, а потом показать их тебе \n' +
                             'Ну что, начнем поиски ?', keyboard=keyboard)

            elif request in ["поиск", "да"]:
                send_message(user_id, 'Пожалуйста подожди...')
                offered_users_info = offered_users_search(user_info)
                random_user_data = get_random_user(offered_users_info, user_id)
                db_add_offered_user_info(random_user_data, user_id)
                random_user.append(random_user_data)
                if random_user_data['id'] not in list_chosen:
                    print(random_user_data['id'])
                    send_message(user_id,
                                 message={random_user_data['first_name'] + ' ' + random_user_data['last_name']},
                                 attachment=get_offered_user_photos(user_id, random_user_data['id']))
                    send_message(user_id, f"Возраст: {random_user_data['age']}")
                    send_message(user_id, f"Ссылка на профиль: {random_user_data['vk_link']}")
                    send_message(user_id, "Занести пользователя в список избранных?", keyboard=keyboard)

                    message_text = loop_bot()
                    if message_text == 'Да':
                        print("AAAAAAA")
                        db_add_fav_user_info(random_user[0])
                        list_chosen.append(random_user[0]['id'])
                        send_message(user_id, "Кандидат занесен в список избранных")
                    elif message_text == 'Нет':
                        print("BBBBBB")
                        db_add_blocked_user_info(random_user[0])
                        list_chosen.append(random_user[0]['id'])
                        send_message(user_id, "Кандидат занесен в черный список")

                    send_message(user_id, "Продолжим ?", keyboard=keyboard)
                else:
                    continue

            elif request == 'избранное':
                send_message(user_id, f"{db_get_fav_users_info(user_id)}")
                send_message(user_id, "Продолжим ?", keyboard=keyboard)

            elif request == 'нет':
                send_message(user_id, 'Что ж, тогда в следующий раз, пока :)')
                break
            else:
                send_message(user_id, 'Для начала работы введите "привет"')


main()
