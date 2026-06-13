# Инструкция по деплою (развертыванию) на сервере

Данное руководство поможет развернуть и запустить проект (Django API + Telegram Bot) на вашем Linux-сервере (Ubuntu/Debian) на порту `8889` с доменом `pechat.lordx.uz` и SSL-сертификатом.

---

## Шаг 1. Подготовка окружения на сервере

Обновите пакеты системы и установите необходимые зависимости:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx git-all -y
```

---

## Шаг 2. Настройка виртуального окружения и установка зависимостей

Перейдите в директорию склонированного проекта (например, `/home/lordx/pechat_bot`):
```bash
cd /home/lordx/pechat_bot

# Создаем виртуальное окружение
python3 -m venv .venv

# Активируем окружение
source .venv/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости для Django и бота
pip install -r backend/requirements.txt
pip install -r bot/requirements.txt

# Устанавливаем Gunicorn для продакшн-запуска Django
pip install gunicorn
```

---

## Шаг 3. Конфигурация файла окружения `.env`

Создайте или отредактируйте файл `.env` в корневой директории `/home/lordx/pechat_bot/.env`:
```ini
# Токен вашего Telegram-бота
TELEGRAM_BOT_TOKEN=7978318477:AAEronfmKCki9Vg-KrWPy-Nbl4TkmHnEwhM

# Настройки Django
SECRET_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ДЛЯ_ПРОДАКШНА_ТУТ
DEBUG=False
ALLOWED_HOSTS=pechat.lordx.uz,127.0.0.1,localhost

# URL бэкенда для бота (указываем ваш домен с https)
BACKEND_URL=https://pechat.lordx.uz
```

---

## Шаг 4. Настройка базы данных и сбор статики Django

При активном виртуальном окружении выполните команды Django:
```bash
cd /home/lordx/pechat_bot/backend

# Применяем миграции базы данных
python manage.py migrate

# Собираем статические файлы (CSS/JS админки) в папку staticfiles
python manage.py collectstatic --noinput

# (Опционально) Наполняем базу начальными данными (если требуется)
python manage.py seed_data
```

---

## Шаг 5. Настройка системных служб (Systemd)

Чтобы Django и бот работали в фоновом режиме стабильно и автоматически запускались при перезагрузке сервера, настроем службы `systemd`.

### 5.1. Служба для Django (Gunicorn)
Создайте файл конфигурации службы:
```bash
sudo nano /etc/systemd/system/pechat_backend.service
```
Вставьте следующий текст (укажите `root`, если запускаете от имени суперпользователя, или `www-data`):
```ini
[Unit]
Description=Pechat Bot Django Backend (Gunicorn)
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/pechat_bot/backend
ExecStart=/var/www/pechat_bot/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8889 config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5.2. Служба для Telegram Bot
Создайте файл конфигурации службы:
```bash
sudo nano /etc/systemd/system/pechat_bot.service
```
Вставьте следующий текст:
```ini
[Unit]
Description=Pechat Bot Telegram Daemon
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/pechat_bot
ExecStart=/var/www/pechat_bot/.venv/bin/python bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5.3. Активация и запуск служб
Выполните команды для перезапуска демона systemd, добавления служб в автозапуск и их старта:
```bash
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable pechat_backend
sudo systemctl enable pechat_bot

# Запускаем службы
sudo systemctl start pechat_backend
sudo systemctl start pechat_bot
```

---

## Шаг 6. Настройка Nginx и домена с SSL (Reverse Proxy)

### 6.1. Создание конфигурации Nginx
Создайте новый конфигурационный файл хоста:
```bash
sudo nano /etc/nginx/sites-available/pechat_bot
```
Вставьте конфигурацию, которая перенаправляет трафик с порта `80` (HTTP) на локальный порт `8889` (где запущен Gunicorn), а также раздает статику и медиафайлы:
```nginx
server {
    listen 80;
    server_name pechat.lordx.uz;

    # Статические файлы Django
    location /static/ {
        alias /home/lordx/pechat_bot/backend/staticfiles/;
    }

    # Медиа-файлы (дизайны, чеки, фото товаров)
    location /media/ {
        alias /home/lordx/pechat_bot/backend/media/;
    }

    # Проксирование всех остальных запросов на Gunicorn (порт 8889)
    location / {
        proxy_pass http://127.0.0.1:8889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте конфигурацию, создав символическую ссылку:
```bash
sudo ln -s /etc/nginx/sites-available/pechat_bot /etc/nginx/sites-enabled/
```
Проверьте Nginx на наличие синтаксических ошибок:
```bash
sudo nginx -t
```
Перезапустите Nginx:
```bash
sudo systemctl restart nginx
```

### 6.2. Установка SSL-сертификата (HTTPS) от Let's Encrypt
Запустите Certbot для автоматического выпуска и привязки SSL к вашему домену `pechat.lordx.uz`:
```bash
sudo certbot --nginx -d pechat.lordx.uz
```
Следуйте интерактивным инструкциям (укажите email, согласитесь с условиями). Certbot автоматически обновит ваш файл конфигурации Nginx, включит HTTPS (порт 443) и настроит редирект со стандартного HTTP на безопасный HTTPS.

---

## Шаг 7. Управление и Мониторинг

Используйте следующие команды для проверки состояния служб и просмотра логов в реальном времени:

* **Проверка статуса служб**:
  ```bash
  sudo systemctl status pechat_backend
  sudo systemctl status pechat_bot
  ```
* **Просмотр логов Django (бэкенда)**:
  ```bash
  journalctl -u pechat_backend.service -f -n 100
  ```
* **Просмотр логов Telegram-бота**:
  ```bash
  journalctl -u pechat_bot.service -f -n 100
  ```
* **Перезапуск приложений после изменения кода**:
  ```bash
  sudo systemctl restart pechat_backend
  sudo systemctl restart pechat_bot
  ```
