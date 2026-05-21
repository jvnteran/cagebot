.PHONY: test lint run db-up db-down load clean

# Run unit tests
test:
	PYTHONPATH=. pytest tests/ -v

# Lint with ruff
lint:
	ruff check .

# Start the Streamlit dashboard (local)
run:
	cd dashboard && streamlit run Overview.py --server.port 8501

# Start PostgreSQL + pgAdmin in Docker
db-up:
	docker compose up -d

# Stop and remove database containers
db-down:
	docker compose down

# Load CSV data into PostgreSQL
load:
	PYTHONPATH=. python etl/load_all.py

# Reset database and reload
clean: db-down
	docker compose down -v
	docker compose up -d
	@echo "Waiting for PostgreSQL..."
	@sleep 3
	PYTHONPATH=. python etl/load_all.py
