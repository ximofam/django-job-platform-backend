# django-job-platform-backend

Frontend here: https://github.com/ximofam/react-native-job-platform.git

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
celery -A configs beat --loglevel=info
```

chạy stripe listen

```
stripe listen --forward-to localhost:8000/api/payments/webhook/stripe/
```
