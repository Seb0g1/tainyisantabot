#!/bin/bash

# Скрипт обновления бота
# Использование: sudo bash update.sh

set -e

BOT_DIR="/opt/santa_bot"
BOT_USER="santabot"

if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Запусти скрипт с sudo: sudo bash update.sh"
    exit 1
fi

echo "🔄 Обновление бота..."

# Остановка бота
echo "⏸️  Остановка бота..."
systemctl stop santa-bot

# Обновление кода
echo "📥 Обновление кода из GitHub..."
cd $BOT_DIR
sudo -u $BOT_USER git pull

# Обновление зависимостей
echo "📚 Обновление зависимостей..."
sudo -u $BOT_USER $BOT_DIR/venv/bin/pip install --upgrade pip
sudo -u $BOT_USER $BOT_DIR/venv/bin/pip install -r $BOT_DIR/requirements.txt

# Запуск бота
echo "🚀 Запуск бота..."
systemctl start santa-bot

# Проверка статуса
sleep 2
if systemctl is-active --quiet santa-bot.service; then
    echo "✅ Бот успешно обновлён и запущен!"
    echo "📊 Статус: systemctl status santa-bot"
else
    echo "❌ Ошибка запуска бота!"
    echo "Проверь логи: journalctl -u santa-bot -n 50"
    exit 1
fi

