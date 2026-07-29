# ESWS containerized stack — common operations.
.PHONY: build up down logs smoke test check-baremetal check-geoserver

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

check-baremetal:  ## Verify install.sh / requirements_py3.txt still install on a clean machine
	docker build -f docker/Dockerfile.baremetal-check -t esws/baremetal-check .

check-geoserver:  ## Verify install.sh's GeoServer step produces a serving GeoServer
	docker build -f docker/Dockerfile.geoserver-check -t esws/geoserver-check .

test: smoke
