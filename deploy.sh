#!/bin/bash

# Скрипт автоматического развёртывания Тайного Санты Бота на Ubuntu
# Использование: bash deploy.sh

set -e  # Остановка при ошибке

echo "🎅 Начинаем развёртывание Тайного Санты Бота..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Запусти скрипт с sudo: sudo bash deploy.sh${NC}"
    exit 1
fi

# Обновление системы
echo -e "${GREEN}📦 Обновление системы...${NC}"
apt-get update
apt-get upgrade -y

# Установка Python и pip
echo -e "${GREEN}🐍 Установка Python и pip...${NC}"
apt-get install -y python3 python3-pip python3-venv git

# Создание пользователя для бота (если не существует)
BOT_USER="santabot"
if ! id "$BOT_USER" &>/dev/null; then
    echo -e "${GREEN}👤 Создание пользователя $BOT_USER...${NC}"
    useradd -m -s /bin/bash $BOT_USER
fi

# Создание директории для бота
BOT_DIR="/opt/santa_bot"
echo -e "${GREEN}📁 Создание директории $BOT_DIR...${NC}"
mkdir -p $BOT_DIR
chown $BOT_USER:$BOT_USER $BOT_DIR

# Клонирование или обновление репозитория
echo -e "${GREEN}📥 Клонирование репозитория...${NC}"
if [ -d "$BOT_DIR/.git" ]; then
    echo "Репозиторий уже существует, обновляем..."
    cd $BOT_DIR
    sudo -u $BOT_USER git pull
else
    echo "Клонируем репозиторий..."
    sudo -u $BOT_USER git clone https://github.com/Seb0g1/tainyisantabot.git $BOT_DIR
fi

# Создание виртуального окружения
echo -e "${GREEN}🔧 Создание виртуального окружения...${NC}"
cd $BOT_DIR
sudo -u $BOT_USER python3 -m venv venv

# Установка зависимостей
echo -e "${GREEN}📚 Установка зависимостей...${NC}"
sudo -u $BOT_USER $BOT_DIR/venv/bin/pip install --upgrade pip
sudo -u $BOT_USER $BOT_DIR/venv/bin/pip install -r $BOT_DIR/requirements.txt

# Создание .env файла (если не существует)
if [ ! -f "$BOT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  Создание .env файла...${NC}"
    echo "BOT_TOKEN=your_bot_token_here" > $BOT_DIR/.env
    chown $BOT_USER:$BOT_USER $BOT_DIR/.env
    chmod 600 $BOT_DIR/.env
    echo -e "${RED}❌ ВАЖНО! Отредактируй $BOT_DIR/.env и добавь токен бота!${NC}"
    echo -e "${YELLOW}   nano $BOT_DIR/.env${NC}"
fi

# Создание systemd service файла
echo -e "${GREEN}⚙️  Создание systemd service...${NC}"
cat > /etc/systemd/system/santa-bot.service << EOF
[Unit]
Description=Тайный Санта Бот v666
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
systemctl daemon-reload

# Включение автозапуска
systemctl enable santa-bot.service

# Запуск бота
echo -e "${GREEN}🚀 Запуск бота...${NC}"
systemctl start santa-bot.service

# Проверка статуса
sleep 2
if systemctl is-active --quiet santa-bot.service; then
    echo -e "${GREEN}✅ Бот успешно запущен!${NC}"
    echo -e "${GREEN}📊 Статус: systemctl status santa-bot${NC}"
    echo -e "${GREEN}📝 Логи: journalctl -u santa-bot -f${NC}"
else
    echo -e "${RED}❌ Ошибка запуска бота!${NC}"
    echo -e "${YELLOW}Проверь логи: journalctl -u santa-bot -n 50${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Развёртывание завершено!${NC}"
echo -e "${YELLOW}⚠️  Не забудь добавить токен бота в $BOT_DIR/.env${NC}"

