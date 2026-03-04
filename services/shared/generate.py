#!/usr/bin/env python3
"""
Скрипт для генерации кода из OpenAPI спецификаций.

Использует datamodel-code-generator для генерации Pydantic моделей.

Запуск:
    python generate.py --service <service_name>
    python generate.py --all
"""

import argparse
import subprocess
import sys
from pathlib import Path

SERVICES = {
    "users": {
        "spec": "openapi/auth.yaml",
        "output": "users/src/api/generated",
    },
    "catalog": {
        "spec": "openapi/catalog.yaml",
        "output": "catalog/src/api/generated",
    },
    "orders": {
        "spec": "openapi/orders.yaml",
        "output": "orders/src/api/generated",
    },
}

SHARED_DIR = Path(__file__).parent


def generate_service(service_name: str) -> bool:
    """Генерирует код для указанного сервиса."""
    if service_name not in SERVICES:
        print(f"❌ Неизвестный сервис: {service_name}")
        print(f"   Доступные сервисы: {', '.join(SERVICES.keys())}")
        return False

    config = SERVICES[service_name]
    spec_path = SHARED_DIR / config["spec"]
    output_path = SHARED_DIR.parent / config["output"]

    if not spec_path.exists():
        print(f"❌ OpenAPI спецификация не найдена: {spec_path}")
        return False

    # Создаем директорию для вывода
    output_path.mkdir(parents=True, exist_ok=True)

    # Добавляем __init__.py
    (output_path / "__init__.py").write_text(
        '"""Сгенерированные модели из OpenAPI спецификации."""\n'
    )

    # Запускаем datamodel-codegen
    cmd = [
        "datamodel-codegen",
        "--input",
        str(spec_path),
        "--output",
        str(output_path / "models.py"),
        "--output-model-type",
        "pydantic-v2.BaseModel",
        "--field-constraints",
        "--strict-types",
        "str",
        "int",
        "float",
        "bool",
        "--snake-case-field",
        "--strip-default-none",
        "--target-python-version",
        "3.11",
    ]

    print(f"🔄 Генерация кода для {service_name}...")
    print(f"   Спецификация: {spec_path}")
    print(f"   Вывод: {output_path}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка генерации:")
            print(result.stderr)
            return False

        print(f"✅ Успешно сгенерировано: {output_path / 'models.py'}")
        return True

    except FileNotFoundError:
        print(
            "❌ datamodel-codegen не найден. Установите: pip install datamodel-code-generator"
        )
        return False


def generate_all() -> bool:
    """Генерирует код для всех сервисов."""
    success = True
    for service_name in SERVICES:
        if not generate_service(service_name):
            success = False
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Генерация кода из OpenAPI спецификаций"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--service", help="Имя сервиса для генерации")
    group.add_argument("--all", action="store_true", help="Генерировать все сервисы")

    args = parser.parse_args()

    if args.all:
        success = generate_all()
    else:
        success = generate_service(args.service)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
