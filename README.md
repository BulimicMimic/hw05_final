## Yatube

### Автор: 
Алаткин Александр

### Описание:
Yatube — блогерская соцсеть с функциями публикации записей и подписки на избранных авторов.

Реализована регистрация и авторизация с верификацией данных, сменой и восстановлением пароля. Есть небольшой фронт с настроенной пагинацией и кешированием. Проект покрыт тестами Unittest.

### Использующиеся технологии:
```
Python 3.9
Django 2.2.16
```

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/BulimicMimic/hw05_final
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
