

.PHONY: clean-settings

clean-settings:
	yq -M 'del(.print_nanny)' ~/.octoprint/config.yaml >  ~/.octoprint/config.yaml

lint:
	black print_nanny tests

dev-install:
	pip install -e .[dev]


nginx:
	docker run -v $(shell pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
		--rm \
		--network=host \
		-it nginx

mjpg-streamer:

	cd ~/projects/mjpg-streamer/mjpg-streamer-experimental && \
	./mjpg_streamer -i "./input_raspicam.so -fps 10" -o "./output_http.so -p 8081 -w /www"