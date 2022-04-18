

.PHONY: clean-settings mypy

PRINT_NANNY_USER ?=leigh

OCTOPRINT_NANNY_STATIC_URL ?= "http://aurora:8000/static/"
OCTOPRINT_NANNY_API_URL ?= "http://aurora:8000/api/"
OCTOPRINT_NANNY_WS_URL ?= "ws://aurora:8000/ws/"

WORKSPACE ?=$(shell pwd)
TMP_DIR ?=$(WORKSPACE)/.tmp
OCTOPRINT_CONFIG_DIR ?=$(WORKSPACE)/.octoprint
PRINTNANNY_CLI_WORKSPACE ?=$(TMP_DIR)/printnanny-cli
PRINTNANNY_CLI_GIT_REPO ?=git@github.com:bitsy-ai/printnanny-cli.git
PRINTNANNY_CLI_GIT_BRANCH ?=main
PRINTNANNY_BIN=$(PRINTNANNY_CLI_WORKSPACE)/target/debug/printnanny-cli
PRINTNANNY_PREFIX=$(TMP_DIR)/local
PRINTNANNY_CONFIG=$(TMP_DIR)/Local.toml
PIP_VERSION=$(shell python -c 'import pip; print(pip.__version__)')
PYTHON_VERSION=$(shell python -c 'import platform; print(platform.python_version())')
PRINTNANNY_PLUGIN_VERSION=$(shell git rev-parse HEAD)

$(TMP_DIR):
	mkdir -p $(TMP_DIR)

$(PRINTNANNY_CLI_WORKSPACE): $(TMP_DIR)
	cd $(TMP_DIR) && git clone --branch $(PRINTNANNY_CLI_GIT_BRANCH) $(PRINTNANNY_CLI_GIT_REPO) || cd $(PRINTNANNY_CLI_WORKSPACE) && git checkout $(PRINTNANNY_CLI_GIT_BRANCH) && git pull

$(PRINTNANNY_CONFIG): $(TMP_DIR)
	TMP_DIR=$(TMP_DIR) \
	WORKSPACE=$(WORKSPACE) \
	HOSTNAME=$(shell cat /etc/hostname) \
	PIP_VERSION=$(PIP_VERSION) \
	PYTHON_VERSION=$(PYTHON_VERSION) \
	PRINTNANNY_PLUGIN_VERSION=$(PRINTNANNY_PLUGIN_VERSION) \
	j2 Local.j2 > $(PRINTNANNY_CONFIG)

.octoprint:
	mkdir .octoprint
mypy:
	mypy octoprint_nanny/

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
	rm -rf $(TMP_DIR)

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
	OCTOPRINT_NANNY_API_URL="${OCTOPRINT_NANNY_API_URL}" \
	OCTOPRINT_NANNY_WS_URL="${OCTOPRINT_NANNY_WS_URL}" \
	OCTOPRINT_NANNY_IOT_DEVICE_REGISTRY="octoprint-devices" \
	OCTOPRINT_NANNY_SNAPSHOT_URL="https://localhost:8080/?action=snapshot" \
	OCTOPRINT_NANNY_HONEYCOMB_DATASET="print_nanny_plugin_sandbox" \
	OCTOPRINT_NANNY_HONEYCOMB_API_KEY="84ed521e04aad193f543d5a078ad2708" \
	OCTOPRINT_NANNY_STATIC_URL="${OCTOPRINT_NANNY_STATIC_URL}" \
	PYTHONASYNCIODEBUG=True \
	OCTOPRINT_NANNY_HONEYCOMB_DEBUG=False \
	octoprint serve

printnanny-cli-debug: $(PRINTNANNY_CLI_WORKSPACE)
	cd $(PRINTNANNY_CLI_WORKSPACE) && cargo build --workspace

printnanny-test-profile:
	cd $(PRINTNANNY_CLI_WORKSPACE) && PRINTNANNY_PREFIX=$(PRINTNANNY_PREFIX) make test-profile

printnanny-dash-debug: printnanny-test-profile
	cd $(PRINTNANNY_CLI_WORKSPACE)/dash && cargo run -- --config $(PRINTNANNY_CONFIG)

octoprint-local: .octoprint printnanny-cli-debug $(PRINTNANNY_CONFIG)
	PRINTNANNY_PROFILE=local \
	PRINTNANNY_BIN="$(PRINTNANNY_BIN)" \
	PRINTNANNY_CONFIG="$(PRINTNANNY_CONFIG)" \
	OCTOPRINT_NANNY_MAX_BACKOFF_TIME=4 \
	OCTOPRINT_NANNY_GCP_PROJECT_ID="print-nanny-sandbox" \
	OCTOPRINT_NANNY_API_URL="${OCTOPRINT_NANNY_API_URL}" \
	OCTOPRINT_NANNY_WS_URL="${OCTOPRINT_NANNY_WS_URL}" \
	OCTOPRINT_NANNY_STATIC_URL="${OCTOPRINT_NANNY_STATIC_URL}" \
	OCTOPRINT_NANNY_HONEYCOMB_DATASET="printnanny_plugin_sandbox" \
	PYTHONASYNCIODEBUG=True \
	OCTOPRINT_NANNY_HONEYCOMB_DEBUG=True \
	octoprint serve --host=0.0.0.0 --port=5001 --basedir $(shell pwd)/.octoprint

octoprint-prod:
	PYTHONASYNCIODEBUG=True octoprint serve --host=0.0.0.0 --port=5000
test:
	pytest --log-level=DEBUG

ci-coverage:
	pytest --cov=./ --cov-report=xml --log-level=INFO

install-git-hooks:
	cp -a hooks/. .git/hooks/