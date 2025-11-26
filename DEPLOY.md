# 🚀 Развёртывание бота на Ubuntu

## Автоматическое развёртывание

### Быстрый старт

1. **Скачай скрипт развёртывания:**
```bash
wget https://raw.githubusercontent.com/Seb0g1/tainyisantabot/main/deploy.sh
chmod +x deploy.sh
```

2. **Запусти скрипт (требуются права root):**
```bash
sudo bash deploy.sh
```

3. **Добавь токен бота:**
```bash
sudo nano /opt/santa_bot/.env
```
Замени `your_bot_token_here` на реальный токен от @BotFather

4. **Перезапусти бота:**
```bash
sudo systemctl restart santa-bot
```

## Ручное развёртывание

### 1. Установка зависимостей

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git
```

### 2. Клонирование репозитория

```bash
git clone https://github.com/Seb0g1/tainyisantabot.git
cd tainyisantabot
```

### 3. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Настройка .env

```bash
cp env.example .env
nano .env
```

Добавь токен бота:
```
BOT_TOKEN=твой_токен_здесь
```

### 5. Запуск через systemd (для работы 24/7)

Создай файл `/etc/systemd/system/santa-bot.service`:

```ini
[Unit]
Description=Тайный Санта Бот v666
After=network.target

[Service]
Type=simple
User=твой_пользователь
WorkingDirectory=/путь/к/боту
Environment="PATH=/путь/к/боту/venv/bin"
ExecStart=/путь/к/боту/venv/bin/python /путь/к/боту/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Активируй и запусти:

```bash
sudo systemctl daemon-reload
sudo systemctl enable santa-bot
sudo systemctl start santa-bot
```

## Управление ботом

### Просмотр статуса
```bash
sudo systemctl status santa-bot
```

### Просмотр логов
```bash
# Все логи
sudo journalctl -u santa-bot

# Последние 50 строк
sudo journalctl -u santa-bot -n 50

# Следить за логами в реальном времени
sudo journalctl -u santa-bot -f
```

### Перезапуск
```bash
sudo systemctl restart santa-bot
```

### Остановка
```bash
sudo systemctl stop santa-bot
```

### Обновление бота

```bash
cd /opt/santa_bot
sudo -u santabot git pull
sudo systemctl restart santa-bot
```

## Структура после развёртывания

```
/opt/santa_bot/
├── main.py
├── database.py
├── config.py
├── requirements.txt
├── .env              # Токен бота (создай вручную)
├── venv/             # Виртуальное окружение
├── santa_bot.db      # База данных (создаётся автоматически)
└── santa_bot.log     # Логи (создаётся автоматически)
```

## Решение проблем

### Бот не запускается

1. Проверь логи: `sudo journalctl -u santa-bot -n 50`
2. Проверь, что токен указан в `.env`
3. Проверь права доступа: `ls -la /opt/santa_bot`

### Бот падает

1. Проверь логи на ошибки
2. Убедись, что все зависимости установлены
3. Проверь, что база данных доступна для записи

### Обновление кода

```bash
cd /opt/santa_bot
sudo -u santabot git pull
sudo systemctl restart santa-bot
```

## Безопасность

- Не коммить `.env` файл в Git
- Используй отдельного пользователя для бота
- Ограничь права доступа к файлам бота
- Регулярно обновляй систему и зависимости

