# Payment Webhook Service (MrKrabsMoney)

Сервіс для надійної обробки вебхуків платіжних систем (Stripe) з підтримкою ідемпотентності через Redis та асинхронною обробкою задач у Celery.

---

## 1. Локальний запуск та перевірка

### Крок 1. Запуск середовища
Переконайтеся, що у вас встановлено Docker та Docker Compose.

```bash
# 1. Клонуйте репозиторій та перейдіть у директорію
cd MrKrabsMoney

# 2. Створіть файл конфігурації .env
cp .env.example .env

# 3. Запустіть усі сервіси в Docker
docker compose up -d --build

```

---

### Крок 2. Створення платежу через API

Створіть новий платіж перед симуляцією вебхука:

#### cURL (Linux / macOS / Git Bash):

```bash
curl --location 'http://localhost:5000/api/v1/payments' \
  --header 'Content-Type: application/json' \
  --data '{
      "amount": 46.15,
      "currency": "usd"
  }'

```

#### PowerShell (Windows):

```powershell
$body = '{"amount": 46.15, "currency": "usd"}'; Invoke-RestMethod -Uri "http://localhost:5000/api/v1/payments" -Method Post -ContentType "application/json" -Body $body

```

---

### Крок 3. Перевірка обробки вебхуків (Stripe CLI)

#### А. Генерація нової події `payment_intent.succeeded`:

```bash
docker compose exec stripe-cli stripe trigger payment_intent.succeeded

```

#### Б. Тестування ідемпотентності (повторна відправка дубліката за Event ID):

```bash
docker compose exec stripe-cli stripe events resend evt_3U1fCXPzfOFb2aiD1f1Drmx2 \
  --api-key sk_test_51...

```

* **Перший запит:** повертає `200 OK` (`{"status": "success"}`) -> передає задачу в Celery.
* **Повторний запит:** повертає `200 OK` (`{"status": "ignored", "reason": "Duplicate event"}`) -> **НЕ** дублює задачу в Celery.

---

### Крок 4. Ручне тестування ендпоінта вебхука

#### cURL (Linux / macOS / Git Bash):

```bash
curl -X POST http://localhost:5000/api/v1/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_test_idempotency_123",
    "type": "payment_intent.succeeded",
    "data": {
      "object": {
        "id": "pi_test_999",
        "status": "succeeded",
        "amount": 4615,
        "currency": "usd"
      }
    }
  }'

```

---

### Крок 5. Перевірка ключів у Redis

```bash
# Переглянути ключі оброблених подій
docker compose exec redis redis-cli KEYS "webhook:stripe:processed:*"

# Перевірити статус конкретної події
docker compose exec redis redis-cli GET "webhook:stripe:processed:evt_test_idempotency_123"

```

---

### Крок 6. Перегляд логів

```bash
# Логи Flask API
docker compose logs -f web

# Логи фонового воркера Celery
docker compose logs -f worker

```

---

## 2. Що зроблено

* **Обробка Stripe Webhooks:** Ендпоінт для прийому подій Stripe, валідації криптографічного підпису (`Stripe-Signature`) та розпарсингу пейлоаду.
* **Ідемпотентність на рівні Redis:** Використання атомарної операції `SET key value NX EX 259200` (TTL 72 години). Це унеможливлює повторну обробку однакових вебхуків при мережевих повторах від Stripe.
* **Асинхронна обробка (Celery):** Швидка відповідь клієнту (`200 OK`) та винесення бізнес-логіки оновлення платежів у фонові таски Celery.
* **Безпечна робота з фінансами:** Збереження грошових сум у центах (цілочисельний тип `int` / `BigInteger`), що виключає помилки округлення `float`.
* **Подвійний захист у БД:** Перевірка стану платежу на рівні транзакції БД перед оновленням статусу (Fallback-ідемпотентність на випадок втрати кешу).
* **Контейнеризація:** Повна ізоляція додатків через Docker Compose (`web`, `worker`, `redis`, `db`, `stripe-cli`).

---

## 3. Складні моменти та майбутні покращення

### З чим було складно:

1. **Специфіка Stripe API та валідація:** Глибокий розбір структури об'єктів Stripe (`charge.updated` vs `payment_intent.succeeded`), а також коректна перевірка підписів під час локального тестування без публічної IP-адреси.
2. **Проектування ідемпотентності:** Визначення оптимальної точки для перевірки дублікатів (до чи після парсингу події) та налаштування збереження станів під час паралельних або повторних викликів.
3. **Вибір формату грошових даних:** Аналіз доцільності використання `Decimal` у БД проти `int` (центи), що вимагало узгодження роботи зі Stripe SDK (який віддає суми в центах) та бази даних.
4. **Незвичність та нюанси роботи з Flask:** Синхронна природа Flask вимагає особливої уваги при роботі з фоновими тасками (Celery) та управлінням контекстом додатка (app_context). Також відсутність вбудованої суворої типізації та автоматичної валідації запитів (на відміну від FastAPI / Pydantic) змусила будувати власну шар-валідацію входних даних та підписів вебхуків.

### Що покращив би / доробив, якби мав більше часу:

* **Асинхронний веб-фреймворк:** Перехід з Flask на **FastAPI** або **Litestar** для кращої продуктивності I/O при високих навантаженнях та автоматичної генерації OpenAPI/Swagger документації.
* **Рейт-лімітинг (Rate Limiting):** Додавання обмеження кількості запитів на ендпоінти (через Redis / `Flask-Limiter` або Nginx) для захисту від DoS-атак.
* **Структуроване логування:** Впровадження JSON-логування (`structlog`) та підключення системи моніторингу/трейсингу (Sentry, OpenTelemetry, Grafana/Loki).
* **Повноцінний брокер повідомлень (RabbitMQ / Kafka):** Заміна використання Redis як брокера Celery на RabbitMQ для більшої надійності доставки повідомлень та підтримки Dead Letter Queue (DLQ) для невдалих тасків.
