

.PHONY: clean-settings

PRINT_NANNY_USER ?= "leigh"

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

yq:
	mkdir -p && wget https://github.com/mikefarah/yq/releases/download/v4.2.0/yq_linux_arm -O ~/.local/bin/yq && chmod +x ~/.local/bin/yq
clean-settings:
	yq -M 'del(.octoprint_nanny)' ~/.octoprint/config.yaml >  ~/.octoprint/config.yaml

lint:
	black setup.py octoprint_nanny tests

dev-install:
	pip install -e .[dev]
	pip install dev-requirements.txt

nginx:
	docker run -v $(shell pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
		--rm \
		--network=host \
		-it nginx

mjpg-streamer:

	cd ~/projects/mjpg-streamer/mjpg-streamer-experimental && \
	./mjpg_streamer -i "./input_raspicam.so -fps 5" -o "./output_http.so -p 8081 -w /www"

clean-dist:
	rm -rf dist/

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean: clean-dist clean-pyc clean-build

sdist: ## builds source package
	python3 setup.py sdist && ls -l dist

bdist_wheel: ## builds wheel package
	python3 setup.py bdist_wheel && ls -l dist

dist: clean-dist sdist bdist_wheel

release: dist
	twine upload dist/*


octoprint-sandbox:
	. .venv/bin/activate && \
	OCTOPRINT_NANNY_MAX_BACKOFF_TIME=30 \
	OCTOPRINT_NANNY_GCP_PROJECT_ID="print-nanny-sandbox" \
	OCTOPRINT_NANNY_API_URL="https://${PRINT_NANNY_USER}.sandbox.print-nanny.com:8000/api/" \
	OCTOPRINT_NANNY_WS_URL="ws://${PRINT_NANNY_USER}.sandbox.print-nanny.com:8000/ws/" \
	OCTOPRINT_NANNY_IOT_DEVICE_REGISTRY="octoprint-devices" \
	OCTOPRINT_NANNY_SNAPSHOT_URL="https://localhost:8080/?action=snapshot" \
	OCTOPRINT_NANNY_HONEYCOMB_DATASET="print_nanny_plugin_sandbox" \
	OCTOPRINT_NANNY_HONEYCOMB_API_KEY="84ed521e04aad193f543d5a078ad2708" \
	PYTHONASYNCIODEBUG=True \
	OCTOPRINT_NANNY_HONEYCOMB_DEBUG=False \
	octoprint serve

octoprint-local:
	. .venv/bin/activate && \
	OCTOPRINT_NANNY_MAX_BACKOFF_TIME=4 \
	OCTOPRINT_NANNY_GCP_PROJECT_ID="print-nanny-sandbox" \
	OCTOPRINT_NANNY_API_URL="http://localhost:8000/api/" \
	OCTOPRINT_NANNY_WS_URL="ws://localhost:8000/ws/" \
	OCTOPRINT_NANNY_IOT_DEVICE_REGISTRY="octoprint-devices" \
	OCTOPRINT_NANNY_SNAPSHOT_URL="http://localhost:8080/?action=snapshot" \
	OCTOPRINT_NANNY_HONEYCOMB_DATASET="print_nanny_plugin_sandbox" \
	OCTOPRINT_NANNY_HONEYCOMB_API_KEY="84ed521e04aad193f543d5a078ad2708" \
	PYTHONASYNCIODEBUG=True \
	OCTOPRINT_NANNY_HONEYCOMB_DEBUG=True \
	octoprint serve

octoprint-prod:
	rm -rf ~/.octoprint && rsync ~/.octoprint-prod ~/.octoprint
	cd ~/projects/OctoPrint && . .venv/bin/activate && octoprint serve
	rsync ~/.octoprint ~/.octoprint-prod

test:
	pytest -p no:warnings --log-level=INFO

offline-ci-test:
	pytest -p no:warnings --log-level=INFO -m "not webapp"

online-ci-test:
	pytest -p no:warnings --log-level=INFO -m "not webapp" -m "not offline"

offline-ci-coverage:
	pytest --cov=./ --cov-report=xml -m "not webapp"

online-ci-coverage:
	pytest --cov=./ --cov-report=xml -m "not webapp" -m "not offline"


install-git-hooks:
	cp -a hooks/. .git/hooks/