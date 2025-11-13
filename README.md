## Flower Shop Monorepo

### Backend (`flowers_api`)

- Django REST API with coupons, delivery slots, saved адресами, gift flow, Telegram + Stripe интеграция.
- Celery (broker по умолчанию `memory://`, можно переопределить `CELERY_BROKER_URL`) обслуживает уведомления/авто-таски.
- Stripe webhooks: `/api/payments/stripe/webhook/` (нужно задать `STRIPE_WEBHOOK_SECRET`).
- Новые эндпоинты: купоны, слоты, автодополнение (DaData/OSM), быстрый заказ, product reviews, CSV/Excel экспорт, timeline событий.

#### Запуск

```bash
cd flowers_api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Celery (опционально):

```bash
set CELERY_BROKER_URL=redis://localhost:6379/0
celery -A flowers_api worker -l info
```

Stripe webhook (dev):

```bash
stripe listen --forward-to localhost:8000/api/payments/stripe/webhook/
```

Автотесты:

```bash
python manage.py test shop.tests.test_orders
```

### Frontend (`flower-shop`)

- React + Vite, PWA (manifest + `sw.js`), контексты корзины, избранного, сравнения.
- Купоны, адресные подсказки, сохранённые адреса, подарочный режим, quick-buy, таймлайн заказов.
- Fuse.js поиск с подсветкой, красочный UI, сравнение, лайки, "недавно смотрели".

```bash
cd flower-shop
npm install
npm run dev
```

### Переменные окружения

Создайте `flowers_api/.env`:

```
SECRET_KEY=your-secret
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
SITE_URL=http://127.0.0.1:8000
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
DADATA_API_KEY=
DADATA_SECRET=
CELERY_BROKER_URL=memory://
```

### E2E Flow

1. Запустите backend + frontend (+ Celery при необходимости).
2. Создайте заказ через UI, примените купон и сохранённый адрес.
3. Для фото доставки используйте ссылку из Telegram (или end-point `/api/orders/photo/<token>/`).
4. Проверяйте timeline на странице заказа.

Все ключевые сценарии (купон, saved address, фото доставки) покрыты unit-тестами (`shop/tests/test_orders.py`).
