# ESWS containerized stack — common operations.
.PHONY: build up down logs smoke test

build:        ## Build the app + dashboard images
	docker compose build

up:           ## Start the full stack in the background
	docker compose up -d

down:         ## Stop the stack and remove volumes
	docker compose down -v

logs:         ## Follow logs from all services
	docker compose logs -f

smoke:        ## Build, start the stack, run the pytest smoke suite, tear down
	./scripts/smoke.sh

test: smoke
