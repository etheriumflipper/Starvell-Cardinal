#!/bin/bash

clear
echo "================================"
echo "Starvell Telegram Bot"
echo "================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 не установлен!"
    echo "Установите Python3: sudo apt install python3"
    exit 1
fi

echo "[INFO] Запуск бота..."
echo ""

python3 main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Бот завершился с ошибкой!"
    echo "Проверьте logs/bot.log для деталей"
    echo ""
    exit 1
fi
