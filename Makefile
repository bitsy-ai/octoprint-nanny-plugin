

.PHONY: clean-settings

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
	black octoprint_nanny tests

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