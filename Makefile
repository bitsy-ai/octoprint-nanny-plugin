

.PHONY: clean-settings mypy

PRINT_NANNY_USER ?=leigh

OCTOPRINT_NANNY_STATIC_URL ?= "http://aurora:8000/static/"
OCTOPRINT_NANNY_API_URL ?= "http://aurora:8000/api/"
OCTOPRINT_NANNY_WS_URL ?= "ws://aurora:8000/ws/"

DEV_MACHINE ?= pn-dev

WORKSPACE ?=$(shell pwd)
TMPDIR ?=$(WORKSPACE)/.tmp
OCTOPRINT_CONFIG_DIR ?=$(WORKSPACE)/.octoprint
PRINTNANNY_WEBAPP_WORKSPACE ?= $(HOME)/projects/octoprint-nanny-webapp
PRINTNANNY_CLI_WORKSPACE ?=$(HOME)/projects/printnanny-cli

PRINTNANNY_CONFD ?= $(TMPDIR)/cfg/conf.d
PRINTNANNY_KEYS ?= $(TMPDIR)/cfg/keys

PRINTNANNY_CLI_GIT_REPO ?=git@github.com:bitsy-ai/printnanny-cli.git
PRINTNANNY_CLI_GIT_BRANCH ?=main
PRINTNANNY_BIN=$(PRINTNANNY_CLI_WORKSPACE)/target/debug/printnanny-cli


PRINTNANNY_CONFIG=$(WORKSPACE)/env/Local.toml
PRINTNANNY_OS_RELEASE=$(TMPDIR)/cfg/os-release

PIP_VERSION=$(shell python -c 'import pip; print(pip.__version__)')
PYTHON_VERSION=$(shell python -c 'import platform; print(platform.python_version())')
PRINTNANNY_PLUGIN_VERSION=$(shell git rev-parse HEAD)

PRINTNANNY_BIN ?= $(TMPDIR)/printnanny-cli/target/debug/printnanny-cli

BITBAKE_RECIPE ?= $(HOME)/projects/poky/meta-bitsy/meta-printnanny/recipes-core/octoprint
PRINTNANNY_WEBAPP_WORKSPACE ?= $(HOME)/projects/octoprint-nanny-webapp
PRINTNANNY_CLI_WORKSPACE ?= $(HOME)/projects/printnanny-cli

$(PRINTNANNY_CONFD):
	mkdir -p $(PRINTNANNY_CONFD)

$(TMPDIR):
	mkdir -p $(TMPDIR)

$(TMPDIR)/cfg:
	mkdir -p $(TMPDIR)/cfg

$(TMPDIR)/workspace:
	mkdir -p $(TMPDIR)/workspace

$(PRINTNANNY_KEYS):
	mkdir -p $(PRINTNANNY_KEYS)

$(PRINTNANNY_CONFIG_DEV): $(TMPDIR)/cfg
	make -C $(PRINTNANNY_WEBAPP_WORKSPACE) dev-config 
	cp $(PRINTNANNY_WEBAPP_WORKSPACE)/.tmp/printnanny.toml $(PRINTNANNY_CONFIG_DEV)

$(PRINTNANNY_CONFIG): $(TMPDIR)
	TMPDIR=$(TMPDIR) \
	WORKSPACE=$(WORKSPACE) \
	HOSTNAME=$(shell cat /etc/hostname) \
	PIP_VERSION=$(PIP_VERSION) \
	PYTHON_VERSION=$(PYTHON_VERSION) \
	PRINTNANNY_PLUGIN_VERSION=$(PRINTNANNY_PLUGIN_VERSION) \
	PRINTNANNY_CONFIG_DEV=$(PRINTNANNY_CONFIG_DEV) \
	PRINTNANNY_CONFD=$(PRINTNANNY_CONFD) \
	PRINTNANNY_KEYS=$(PRINTNANNY_KEYS) \
	PRINTNANNY_OS_RELEASE=$(PRINTNANNY_OS_RELEASE) \
	OCTOPRINT_CONFIG_DIR=$(OCTOPRINT_CONFIG_DIR) \
	OCTOPRINT_VENV_DIR=$(PWD)/.venv \
	FINGERPRINT=$(shell openssl md5 -c .tmp/local/keys/ec_public.pem | cut -f2 -d ' ') \
	j2 Local.j2 > $(PRINTNANNY_CONFIG)

$(PRINTNANNY_OS_RELEASE): $(TMPDIR)/cfg
	cp tests/fixtures/os-release $(PRINTNANNY_OS_RELEASE)

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
	rm -rf $(TMPDIR)

clean-cfg:
	rm -rf $(TMPDIR)/cfg

clean-workspace:
	rm -rf $(TMPDIR)/workspace

sdist: ## builds source package
	python3 setup.py sdist && ls -l dist

bdist_wheel: ## builds wheel package
	python3 setup.py bdist_wheel && ls -l dist

dist: clean-dist sdist bdist_wheel

release: dist
	twine upload dist/*

# simulate experience of installing OctoPrint-Nanny on unsupported OS
dev-other-os: .octoprint
	octoprint serve --host=0.0.0.0 --port=5001 --basedir $(shell pwd)/.octoprint


printnanny-cli-debug: $(PRINTNANNY_CLI_WORKSPACE)
	cd $(PRINTNANNY_CLI_WORKSPACE) && cargo build --workspace
# setup: $(PRINTNANNY_OS_RELEASE) printnanny-cli-debug $(PRINTNANNY_CONFD) $(PRINTNANNY_CONFIG) $(PRINTNANNY_CONFIG_DEV)
# 	PRINTNANNY_CONFIG=$(PRINTNANNY_CONFIG) $(PRINTNANNY_BIN) -vvv config sync

# dev-events-sub: setup $(TMPDIR)/ca-certs
# 	PRINTNANNY_CONFIG=$(PRINTNANNY_CONFIG) $(PRINTNANNY_BIN) -vvv event subscribe

# dev-events-pub: setup$(TMPDIR)/ca-certs
# 	PRINTNANNY_CONFIG=$(PRINTNANNY_CONFIG) $(PRINTNANNY_BIN) -vvv event publish

$(TMPDIR)/PrintNanny-$(DEV_MACHINE).zip: $(TMPDIR)
	cp $(PRINTNANNY_WEBAPP_WORKSPACE)/.tmp/PrintNanny-$(DEV_MACHINE).zip $(TMPDIR)/PrintNanny-$(DEV_MACHINE).zip

devconfig: $(TMPDIR)/PrintNanny-$(DEV_MACHINE).zip printnanny-cli-debug
	echo 
	PRINTNANNY_CONFIG=$(PRINTNANNY_CONFIG) $(PRINTNANNY_BIN) -vvv config init

dev: .octoprint
	PRINTNANNY_BIN="$(PRINTNANNY_BIN)" \
	PRINTNANNY_CONFIG="$(PRINTNANNY_CONFIG)" \
	PRINTNANNY_DEBUG=True \
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

