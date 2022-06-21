

.PHONY: clean-settings mypy

PRINT_NANNY_USER ?=leigh

OCTOPRINT_NANNY_STATIC_URL ?= "http://aurora:8000/static/"
OCTOPRINT_NANNY_API_URL ?= "http://aurora:8000/api/"
OCTOPRINT_NANNY_WS_URL ?= "ws://aurora:8000/ws/"

WORKSPACE ?=$(shell pwd)
TMP_DIR ?=$(WORKSPACE)/.tmp
OCTOPRINT_CONFIG_DIR ?=$(WORKSPACE)/.octoprint
PRINTNANNY_WEBAPP_WORKSPACE ?= $(HOME)/projects/octoprint-nanny-webapp

PRINTNANNY_CONFD ?= $(TMP_DIR)/cfg/conf.d
PRINTNANNY_KEYS ?= $(TMP_DIR)/cfg/keys

PRINTNANNY_LICENSE_JSON ?= $(PRINTNANNY_WEBAPP_WORKSPACE)/.tmp/license.json
PRINTNANNY_CLI_WORKSPACE ?=$(TMP_DIR)/workspace/printnanny-cli
PRINTNANNY_CLI_GIT_REPO ?=git@github.com:bitsy-ai/printnanny-cli.git
PRINTNANNY_CLI_GIT_BRANCH ?=main
PRINTNANNY_BIN=$(PRINTNANNY_CLI_WORKSPACE)/target/debug/printnanny-cli
PRINTNANNY_CONFIG=$(TMP_DIR)/cfg/Local.toml
PRINTNANNY_OS_RELEASE=$(TMP_DIR)/cfg/os-release

PIP_VERSION=$(shell python -c 'import pip; print(pip.__version__)')
PYTHON_VERSION=$(shell python -c 'import platform; print(platform.python_version())')
PRINTNANNY_PLUGIN_VERSION=$(shell git rev-parse HEAD)

PRINTNANNY_BIN ?= $(TMP_DIR)/printnanny-cli/target/debug/printnanny-cli

JANUS_EDGE_HOSTNAME ?= localhost
JANUS_API_TOKEN ?= janustoken

BITBAKE_RECIPE ?= $(HOME)/projects/poky/meta-bitsy/meta-printnanny/recipes-core/python3-octoprint-nanny

$(PRINTNANNY_CONFD):
	mkdir -p $(PRINTNANNY_CONFD)

$(TMP_DIR):
	mkdir -p $(TMP_DIR)

$(TMP_DIR)/cfg:
	mkdir -p $(TMP_DIR)/cfg

$(TMP_DIR)/workspace:
	mkdir -p $(TMP_DIR)/workspace

$(PRINTNANNY_KEYS):
	mkdir -p $(PRINTNANNY_KEYS)
	$(PRINTNANNY_BIN) generate-keys --output $(PRINTNANNY_KEYS)

$(PRINTNANNY_CLI_WORKSPACE): $(TMP_DIR)/workspace
	cd $(TMP_DIR)/workspace && git clone --branch $(PRINTNANNY_CLI_GIT_BRANCH) $(PRINTNANNY_CLI_GIT_REPO) || (cd $(PRINTNANNY_CLI_WORKSPACE) && git checkout $(PRINTNANNY_CLI_GIT_BRANCH) && git pull)

$(PRINTNANNY_CONFIG): $(TMP_DIR)
	TMP_DIR=$(TMP_DIR) \
	WORKSPACE=$(WORKSPACE) \
	HOSTNAME=$(shell cat /etc/hostname) \
	PIP_VERSION=$(PIP_VERSION) \
	PYTHON_VERSION=$(PYTHON_VERSION) \
	PRINTNANNY_PLUGIN_VERSION=$(PRINTNANNY_PLUGIN_VERSION) \
	PRINTNANNY_LICENSE_JSON=$(PRINTNANNY_LICENSE_JSON) \
	PRINTNANNY_CONFD=$(PRINTNANNY_CONFD) \
	PRINTNANNY_KEYS=$(PRINTNANNY_KEYS) \
	PRINTNANNY_OS_RELEASE=$(PRINTNANNY_OS_RELEASE) \
	FINGERPRINT=$(shell openssl md5 -c .tmp/local/keys/ec_public.pem | cut -f2 -d ' ') \
	j2 Local.j2 > $(PRINTNANNY_CONFIG)

$(PRINTNANNY_OS_RELEASE): $(TMP_DIR)/cfg
	cp tests/fixtures/os-release $(TMP_DIR)/os-release

.octoprint:
	mkdir .octoprint


mypy:
	mypy octoprint_nanny/

clean-coverage:
	rm -rf .coverage
.coverage:
	mkdir -p .coverage

mypy-coverage: clean-coverage .coverage
	mypy octoprint_nanny/ \
		--cobertura-xml-report .coverage/ 


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

clean-dist:
	rm -rf dist/

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean: clean-dist clean-pyc clean-build
	rm -rf $(TMP_DIR)

clean-cfg:
	rm -rf $(TMP_DIR)/cfg

clean-workspace:
	rm -rf $(TMP_DIR)/workspace

sdist: ## builds source package
	python3 setup.py sdist && ls -l dist

bdist_wheel: ## builds wheel package
	python3 setup.py bdist_wheel && ls -l dist

dist: clean-dist sdist bdist_wheel

release: dist
	twine upload dist/*

printnanny-cli-debug: $(PRINTNANNY_CLI_WORKSPACE)
	cd $(PRINTNANNY_CLI_WORKSPACE) && cargo build --workspace

# simulate experience of installing OctoPrint-Nanny on unsupported OS
dev-other-os: .octoprint
	octoprint serve --host=0.0.0.0 --port=5001 --basedir $(shell pwd)/.octoprint

check-license: $(PRINTNANNY_OS_RELEASE) printnanny-cli-debug $(PRINTNANNY_KEYS) $(PRINTNANNY_CONFD) $(PRINTNANNY_CONFIG)
	PRINTNANNY_CONFIG="$(PRINTNANNY_CONFIG)" \
	strace $(PRINTNANNY_BIN) -vvv check-license

dev: .octoprint check-license
	PRINTNANNY_BIN="$(PRINTNANNY_BIN)" \
	PRINTNANNY_CONFIG="$(PRINTNANNY_CONFIG)" \
	PYTHONASYNCIODEBUG=True \
	octoprint serve --host=0.0.0.0 --port=5001 --basedir $(shell pwd)/.octoprint

test:
	pytest --log-level=DEBUG

ci-coverage:
	pytest --cov=./ --cov-report=xml --log-level=INFO

install-git-hooks:
	cp -a hooks/. .git/hooks/

bitbake:
	pipoe --package octoprint-nanny --python python3 --outdir $(BITBAKE_RECIPE) --default-license AGPLv3
	find $(BITBAKE_RECIPE) -type f -exec sed -i.bak "s/RDEPENDS_${PN}/RDEPENDS:${PN}/g" {} \;
