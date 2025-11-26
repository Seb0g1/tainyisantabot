# 📤 Загрузка проекта на GitHub

## Шаги для загрузки на GitHub

### 1. Инициализация Git репозитория

```bash
git init
```

### 2. Добавление всех файлов

```bash
git add .
```

### 3. Первый коммит

```bash
git commit -m "first commit"
```

### 4. Переименование ветки в main

```bash
git branch -M main
```

### 5. Добавление удалённого репозитория

```bash
git remote add origin https://github.com/Seb0g1/tainyisantabot.git
```

### 6. Загрузка на GitHub

```bash
git push -u origin main
```

## Полная последовательность команд

```bash
# Инициализация
git init

# Добавление файлов
git add .

# Коммит
git commit -m "first commit"

# Переименование ветки
git branch -M main

# Добавление удалённого репозитория
git remote add origin https://github.com/Seb0g1/tainyisantabot.git

# Загрузка
git push -u origin main
```

## Если репозиторий уже существует

Если на GitHub уже есть файлы (например, README.md), используй:

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## Обновление кода

После изменений:

```bash
git add .
git commit -m "Описание изменений"
git push
```

