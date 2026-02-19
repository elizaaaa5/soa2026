# Multi-stage build для минимизации размера образа

# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Установка зависимостей сборки
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /build

# Копируем requirements
COPY src/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Создаем пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Рабочая директория
WORKDIR /app

# Копируем установленные зависимости из builder stage
COPY --from=builder /root/.local /root/.local

# Убедимся, что скрипты в PATH находятся в нужном месте
ENV PATH=/root/.local/bin:$PATH

# Делаем скрипты исполняемыми
RUN chmod +x /root/.local/bin/* || true

# Копируем исходный код
COPY src/ .

# Меняем владельца на appuser
RUN chown -R appuser:appuser /app

# Переключаемся на пользователя
USER root

# Открываем порт 8000
EXPOSE 8000

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    SERVICE_NAME=users-service \
    SERVICE_VERSION=1.0.0 \
    HOST=0.0.0.0 \
    PORT=8000

# Команда запуска (используем python -m для избежания проблем с правами)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
