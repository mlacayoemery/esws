# ESWS containerized stack — common operations.
.PHONY: build up down logs smoke test demo demo-data check-baremetal check-geoserver

build:        ## Build the app + dashboard images
	docker compose build

up:           ## Start the full stack in the background
	docker compose up -d

down:         ## Stop the stack and remove volumes
	docker compose down -v

logs:         ## Follow logs from all services
	docker compose logs -f

unit:         ## Run the tests that need neither the stack nor InVEST (what CI runs)
	python3 -m pytest tests/unit -q

smoke:        ## Build, start the stack, run the pytest smoke suite, tear down
	./scripts/smoke.sh

smoke-demo:   ## smoke, but with the demo data loaded so no test skips
	DEMO=1 ./scripts/smoke.sh

demo-data:    ## Download + unpack the InVEST sample datasets (cached, ~380MB)
	./scripts/fetch_invest_samples.sh

demo: demo-data  ## Load the demo: publish sample data and register it in the dashboard
	docker compose up -d
	# `run` (not `exec`) so the micromamba entrypoint puts python on PATH.
	docker compose run --rm --no-deps wps python scripts/load_demo.py

check-baremetal:  ## Verify install.sh / requirements_py3.txt still install on a clean machine
	docker build -f docker/Dockerfile.baremetal-check -t esws/baremetal-check .

check-geoserver:  ## Verify install.sh's GeoServer step produces a serving GeoServer
	docker build -f docker/Dockerfile.geoserver-check -t esws/geoserver-check .

test: smoke
