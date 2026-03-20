# Makefile для управления проектом
# SOA2026 - Marketplace Architecture

# Цвета для красивого вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help up down logs restart health likec4-serve likec4-build clean test generate

# Default target
.DEFAULT_GOAL := help

help:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  SOA2026 - Marketplace Architecture$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Users Service (Docker):$(NC)"
	@echo "  make up              - Запустить Users Service"
	@echo "  make down            - Остановить Users Service"
	@echo "  make restart         - Перезапустить Users Service"
	@echo "  make logs            - Просмотреть логи Users Service"
	@echo "  make health          - Проверить health endpoint"
	@echo ""
	@echo "$(GREEN)C4 Diagram (likeC4):$(NC)"
	@echo "  make likec4-serve    - Запустить likeC4 web server"
	@echo "  make likec4-build    - Сгенерировать диаграмму в статическом виде"
	@echo ""
	@echo "$(GREEN)Other:$(NC)"
	@echo "  make clean           - Очистить все контейнеры и образы"
	@echo "  make test            - Запустить тесты"
	@echo "  make generate        - Сгенерировать код из OpenAPI спецификаций"
	@echo ""

# Users Service
up:
	@echo "$(BLUE)Запуск Users Service...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Users Service запущен на http://localhost:8000$(NC)"
	@sleep 2
	@make health

down:
	@echo "$(BLUE)Остановка Users Service...$(NC)"
	@cd services/users && docker-compose down
	@echo "$(GREEN)Users Service остановлен$(NC)"

restart:
	@echo "$(BLUE)Перезапуск Users Service...$(NC)"
	@cd services/users && docker-compose restart
	@echo "$(GREEN)Users Service перезапущен$(NC)"
	@sleep 2
	@make health

logs:
	@echo "$(BLUE)Логи Users Service:$(NC)"
	@cd services/users && docker-compose logs -f

health:
	@echo "$(BLUE)Проверка health endpoint...$(NC)"
	@response=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health); \
	if [ "$$response" = "200" ]; then \
		echo "$(GREEN)Health check OK (200 OK)$(NC)"; \
		curl -s http://localhost:8000/health; \
		echo ""; \
	else \
		echo "$(RED)Health check FAILED (HTTP $$response)$(NC)"; \
		exit 1; \
	fi

# C4 Diagram (likeC4)
likec4-serve:
	@echo "$(BLUE)Запуск likeC4 web server...$(NC)"
	@echo "$(GREEN)Открыть в браузере: http://localhost:5173$(NC)"
	@docker run --rm -p 5173:5173 -v $$(pwd):/work -w /work likec4/likec4:latest serve docs

likec4-build:
	@echo "$(BLUE)Генерация C4 диаграммы...$(NC)"
	@docker run --rm -v $$(pwd):/work -w /work likec4/likec4:latest build docs -o .likec4
	@echo "$(GREEN)Диаграмма сгенерирована в .likec4/$(NC)"

# Other
clean:
	@echo "$(BLUE)Очистка всех контейнеров и образов...$(NC)"
	@cd services/users && docker-compose down --rmi all -v
	@echo "$(GREEN)Очистка завершена$(NC)"

test:
	@echo "$(BLUE)Запуск тестов...$(NC)"
	uv run pytest tests/ -v --tb=short

generate:
	@echo "$(BLUE)Генерация кода из OpenAPI спецификаций...$(NC)"
	@echo "$(GREEN)Генерация моделей для Catalog Service...$(NC)"
	@cd services/catalog && uv run datamodel-codegen --input ../shared/openapi/catalog.yaml --output src/api/generated/models.py --input-file-type openapi
	@echo "$(GREEN)Генерация моделей для Orders Service...$(NC)"
	@cd services/orders && uv run datamodel-codegen --input ../shared/openapi/orders.yaml --output src/api/generated/models.py --input-file-type openapi
	@echo "$(GREEN)Код успешно сгенерирован$(NC)"
