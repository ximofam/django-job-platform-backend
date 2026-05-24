# django-job-platform-backend

using django, djangorestframework to build api

cách chạy docker

```
docker compose up -d
```

cách đóng docker

```
docker compose down
```

cách chạy celery

```
celery -A configs worker --loglevel=info --pool=solo
```