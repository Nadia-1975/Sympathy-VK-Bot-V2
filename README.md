## Запуск программы:
1.	Установка необходимых библиотек:
```
    pip install vk_api
    pip install psycopg2
    pip install sqlalchemy
    pip install sqlalchemy_utils
```
2.  Учетные данные необходимые для работы бота находятся в файле config.json, реализовано считывание этих данных ботом при запуске
3.  Запуск производится из файла main.py
3.	Взаимодействие с ботом начинается после написания команды "привет". Далее появляются 3 копки "Избранное", "Да", "Нет"
## Входные данные
   Id пользователя в ВК, для которого мы ищем пару, а так же его город и возраст. Сервис автоматическ получает его при написании команды "привет".
## Взаимодействие с ботом
1. Все взаимодействие с ботом осуществляется через кнопки меню. Запуск бота осуществляется с помощью     написание команды "привет" в чат группы.
2. Бот ищет людей противоположного пола в городе пользователя с разницой в возрасте +/- 5 лет
3. Люди не указавшие или скрывшие свою полную дату рождения не попадают в список предложений пользователю
4. Люди с закрытым профилем не попадают в список предложений пользователю
5. Люди в отношениях (если указан соответствующий статус) не попадают в список предложений пользователю
