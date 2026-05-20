lint:
	python -m ruff check .

test:
	python -m pytest -q

compose-check:
	docker compose config
