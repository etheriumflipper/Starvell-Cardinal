#!/bin/bash

echo "================================"
echo "Starvell Bot - Setup"
echo "================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 не установлен!"
    echo "Установите Python3: sudo apt install python3 python3-pip"
    exit 1
fi

echo "Python версия: $(python3 --version)"
echo ""
echo "Устанавливаю зависимости..."
echo ""

# Обновление pip
python3 -m pip install --upgrade pip

# Установка зависимостей
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Ошибка при установке зависимостей!"
    exit 1
fi

echo ""
echo "================================"
echo "Установка завершена!"
echo "================================"
echo ""
echo "Теперь запустите: ./start.sh"
echo "Или: python3 main.py"
