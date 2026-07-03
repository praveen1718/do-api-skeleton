.PHONY: install dev test lint run docker-build docker-run deploy

install:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

test:
	pytest -q

lint:
	ruff check .

docker-build:
	docker build -t ingestion-api:local .

docker-run:
	docker run --rm -p 8080:8080 -e APP_ENVIRONMENT=local ingestion-api:local

# Requires: doctl auth init  (done once with the token DO gives you)
deploy:
	doctl apps create --spec .do/app.yaml
