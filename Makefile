.PHONY: check test test-e2e lint format typecheck dead-code proto cli build

DOCKER_IMAGE = ajax-cobranded-dev
DOCKER_RUN = docker run --rm -v $(PWD):/app -w /app $(DOCKER_IMAGE)

build-docker:
	docker build -f Dockerfile.dev -t $(DOCKER_IMAGE) .

check: lint format-check typecheck test dead-code
	@echo "All checks passed."

test:
	pytest tests/unit/ -v --cov=custom_components/ajax_cobranded --cov-fail-under=80 --cov-report=term-missing

test-e2e:
	pytest tests/e2e/ -v -m "e2e and not destructive"

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy custom_components/ajax_cobranded/ --ignore-missing-imports --exclude 'proto/'

dead-code:
	vulture custom_components/ajax_cobranded/ vulture_whitelist.py --exclude custom_components/ajax_cobranded/proto/

proto:
	bash scripts/compile_protos.sh

cli:
	python scripts/test_connection.py
