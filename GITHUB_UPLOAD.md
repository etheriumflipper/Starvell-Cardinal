# 📤 Инструкция по загрузке на GitHub

## ✅ Проект Starvell Cardinal v0.1 готов к загрузке!

### Что было проверено:
- ✅ Все Python файлы скомпилированы без ошибок
- ✅ Структура проекта корректна
- ✅ .gitignore настроен (конфиги и логи не попадут в репозиторий)
- ✅ .gitattributes создан (правильные переводы строк для разных ОС)
- ✅ README.md дополнен инструкциями по установке на Linux
- ✅ Созданы shell-скрипты setup.sh и start.sh для Linux

---

## 🚀 Как загрузить на GitHub

### Вариант 1: Через GitHub Desktop (проще)

1. Скачайте и установите [GitHub Desktop](https://desktop.github.com/)
2. Войдите в свой GitHub аккаунт
3. Нажмите `File` → `Add Local Repository`
4. Выберите папку с проектом
5. Нажмите `Publish repository`
6. Снимите галочку "Keep this code private" если хотите публичный репозиторий
7. Нажмите `Publish Repository`

### Вариант 2: Через командную строку

1. Откройте терминал в папке проекта:
   ```bash
   cd путь/к/Starvell-cardinal
   ```

2. Инициализируйте git репозиторий:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Starvell Cardinal v0.1"
   ```

3. Создайте репозиторий на GitHub:
   - Перейдите на https://github.com/new
   - Название: `Starvell-cardinal`
   - Описание: `Telegram bot для автоматизации Starvell.com`
   - Выберите Public или Private
   - НЕ создавайте README, .gitignore, license (они уже есть)
   - Нажмите `Create repository`

4. Свяжите локальный репозиторий с GitHub:
   ```bash
   git remote add origin https://github.com/ВАШ_USERNAME/Starvell-cardinal.git
   git branch -M main
   git push -u origin main
   ```

---

## 📦 Установка с GitHub (для пользователей)

После загрузки, пользователи смогут установить бота так:

### Linux:
```bash
git clone https://github.com/ВАШ_USERNAME/Starvell-cardinal.git
cd Starvell-cardinal
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```

### Windows:
```bash
git clone https://github.com/ВАШ_USERNAME/Starvell-cardinal.git
cd Starvell-cardinal
Setup.bat
Start.bat
```

### Или одной командой (Linux):
```bash
git clone https://github.com/ВАШ_USERNAME/Starvell-cardinal.git && cd Starvell-cardinal && pip3 install -r requirements.txt && python3 main.py
```

---

## ⚠️ Важно перед загрузкой

### Убедитесь что НЕ загружаете:
- ❌ `configs/_main.cfg` - содержит токены и пароли
- ❌ `storage/` - личные данные
- ❌ `logs/` - логи с информацией
- ❌ `__pycache__/` - кеш Python

Все это уже исключено в `.gitignore`, но проверьте:
```bash
git status
```

Если видите эти файлы в списке - НЕ загружайте!

---

## 🔧 Обновление репозитория

После внесения изменений:

```bash
git add .
git commit -m "Описание изменений"
git push
```

---

## 📝 Рекомендации

1. **Создайте Release:**
   - После загрузки перейдите в `Releases` → `Create a new release`
   - Tag: `v0.1`
   - Title: `Starvell Cardinal v0.1`
   - Описание: основные возможности

2. **Добавьте Topics на GitHub:**
   - `telegram-bot`
   - `python`
   - `aiogram`
   - `starvell`
   - `automation`

3. **Настройте GitHub Pages** (опционально):
   - Settings → Pages
   - Source: Deploy from branch `main`
   - Folder: `/docs`

---

## ✅ Готово!

После загрузки ваш бот будет доступен по ссылке:
```
https://github.com/ВАШ_USERNAME/Starvell-cardinal
```

Пользователи смогут установить его командой:
```bash
git clone https://github.com/ВАШ_USERNAME/Starvell-cardinal.git
```
