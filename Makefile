PY := /home/ai1/anaconda3/envs/p312/bin/python

.PHONY: dev dev-api dev-web dev-bot check migrate generate-client

dev:
	@echo "Run 'make dev-api', 'make dev-web', and 'make dev-bot' in separate terminals."

dev-api:
	cd backend && $(PY) -m uvicorn app.main:app --reload

dev-web:
	cd web && npm run dev

dev-bot:
	cd backend && $(PY) -m app.bot.main

check:
	cd backend && $(PY) -m ruff check .
	cd backend && $(PY) -m pytest
	cd web && npx tsc --noEmit

migrate:
	cd backend && $(PY) -m alembic upgrade head

generate-client:
	cd backend && $(PY) -m scripts.export_openapi
	cd web && npx openapi-typescript-codegen --input ../backend/openapi.json --output src/lib/api --client fetch
