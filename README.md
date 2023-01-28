# Черновик Readme1
# praktikum_new_diplom
# Проект Foodgram

Проект Foodgram собирает отзывы пользователей на различные произведения такие как
фильмы, книги и музыка.

## Описание проекта:

API Foodgram позволяет работать со следующими сущностями:

* JWT-токен (Auth): отправить confirmation_code на переданный email, получить
  JWT-токен
  в обмен на email и confirmation_code;
* Пользователи (Users): получить список всех пользователей, создать
  пользователя,
  получить пользователя по username, изменить данные пользователя по username,
  удалить
  пользователя по username, получить данные своей учётной записи, изменить
  данные своей учётной записи;
* Произведения (Titles), к которым пишут отзывы: получить список всех объектов,
  создать
  произведение для отзывов, информация об объекте, обновить информацию об
  объекте, удалить произведение.
  пользователя по username, получить данные своей учётной записи, изменить
  данные своей учётной записи;
* Категории (Categories) произведений: получить список всех категорий, создать
  категорию, удалить категорию;
* Жанры (Genres): получить список всех жанров, создать жанр, удалить жанр;
* Отзывы (Review): получить список всех отзывов, создать новый отзыв, получить
  отзыв по id,
  частично обновить отзыв по id, удалить отзыв по id;
* Комментарии (Comments) к отзывам: получить список всех комментариев к отзыву
  по id, создать
  новый комментарий для отзыва, получить комментарий для отзыва по id, частично
  обновить комментарий к отзыву по id, удалить комментарий к отзыву по id.

## Стек технологий:

* [Python 3.7+](https://www.python.org/downloads/)
* [Django 2.2.16](https://www.djangoproject.com/download/)
* [Django Rest Framework 3.12.4](https://pypi.org/project/djangorestframework/#files)
* [Pytest 6.2.4](https://pypi.org/project/pytest/)
* [Simple-JWT 1.7.2](https://pypi.org/project/djangorestframework-simplejwt/)
* [pytest 6.2.4](https://pypi.org/project/pytest/)
* [pytest-pythonpath 0.7.3](https://pypi.org/project/pytest-pythonpath/)
* [pytest-django 4.4.0](https://pypi.org/project/pytest-django/)
* [djangorestframework-simplejwt 4.7.2](https://pypi.org/project/djangorestframework-simplejwt/)
* [Pillow 9.2.0](https://pypi.org/project/Pillow/)
* [PyJWT 2.1.0](https://pypi.org/project/PyJWT/)
* [requests 2.26.0](https://pypi.org/project/requests/)
* [nginx](https://nginx.org/ru/)
* [PostgreSQL](https://www.postgresql.org)

## Workflow:

* Тестирование проекта (pytest, flake8).
* Сборка и публикация образа на DockerHub.
* Автоматический деплой на удаленный сервер.
* Отправка уведомления в телеграм-чат.

## Как запустить проект

### Клонировать репозиторий

```
git clone git@github.com:LevLM/foodgram-project-react.git
```

#### Выполните вход на свой удаленный сервер

#### Установите docker на сервер(https://docs.docker.com/get-docker/)

#### Установите docker-compose на сервер(https://docs.docker.com/compose/install/linux/#install-using-the-repository)


### Шаблон наполнения env-файла (виртуальное окружение):

Данные внести в файл ".env", поместить его в папке Infra (где находится файл docker-compose.yaml)
Перечень переменных и дефолтных значений размещен в файле

```
.env.sample
```


### Запускаем на сервере через docker-compose 

#### Собрать статические файлы в STATIC_ROOT

```
sudo docker compose exec web python3 manage.py collectstatic --noinput
```

#### Применить миграции

```
sudo docker compose exec web python3 manage.py migrate --noinput
```

#### Заполнить базу данных

```
sudo docker compose exec web python3 manage.py loaddata fixtures.json
```

#### Создать суперпользователя Django

```
sudo docker compose exec web python manage.py createsuperuser
```


#### Проект будет доступен по адресу

```
http://158.160.43.47/admin

http://158.160.43.47/api/v1/[]
```

#### Документация API

```
http://158.160.43.47/redoc/
```

#### [Образ на DockerHub]

```
https://hub.docker.com/repository/docker/levlm/foodgram
```
