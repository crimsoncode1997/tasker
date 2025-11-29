FROM python:3.11-slim

# Важливо: вимикаємо буферизацію (щоб логи відразу йшли в Cloud Logging)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Встановлюємо системні залежності (gcc потрібен для деяких пітон-пакетів)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Створюємо користувача ЗАЗДАЛЕГІДЬ
RUN useradd --create-home --shell /bin/bash app

# Копіюємо requirements і ставимо пакети
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копіюємо код і ВІДРАЗУ передаємо права користувачу app
# Це важливо, щоб уникнути помилок доступу (Permission denied)
COPY --chown=app:app . .

# Перемикаємось на юзера
USER app

EXPOSE 8000

# ✅ ГОЛОВНЕ ВИПРАВЛЕННЯ:
# 1. Запускаємо через "python -m uvicorn" (це гарантує, що модуль знайдеться)
# 2. Прибрали "--reload" (це продакшен!)
# 3. Додали "--proxy-headers" (потрібно, бо Cloud Run стоїть за балансувальником)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]