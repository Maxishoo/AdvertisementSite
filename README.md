# AdvertisementSite

Бэкенд сервис для сайта с объявлениями на FastAPI и PostgreSQL с поддержкой поиска, фильтрации, тегов и модерации. Оптимизирован с помощью индексов, контейнеризован через Docker Compose.

# Запуск проекта

1. Нужно склонировать репозиторий
```bash
https://github.com/Maxishoo/AdvertisementSite.git
```
2. Запускаем сборку контейнеров
```bash
docker-compose up --build
```
3. Запускаем скрипт автоматического наполнения бд тестовыми данными(загрузка может занимать несколько минут)
```bash
docker exec fastapi_app python scripts/generate_data.py
```

# Сброс базы данных
1. Очищаем контейнеры
```bash
docker-compose down -v   
```
2. Билдим заново
```bash
docker-compose up --build
```

Удачи:)