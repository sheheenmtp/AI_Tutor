PYTHON ?= python3
BACKEND_PYTHON := backend/.venv/bin/python

.PHONY: setup setup-backend setup-frontend db-up db-down seed dev lint build

setup: setup-backend setup-frontend

setup-backend:
	$(PYTHON) -m venv backend/.venv
	$(BACKEND_PYTHON) -m pip install --upgrade pip
	$(BACKEND_PYTHON) -m pip install -r backend/requirements.txt

setup-frontend:
	npm ci --prefix frontend

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose down

seed:
	cd backend && .venv/bin/python -c 'from models import init_db; init_db()'
	cd backend && .venv/bin/python seed_data.py

dev:
	./run.sh

lint:
	$(BACKEND_PYTHON) -m compileall -q backend
	npm run lint --prefix frontend

build:
	npm run build --prefix frontend
