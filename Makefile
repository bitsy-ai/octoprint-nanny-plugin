

.PHONY: clean-settings

clean-settings:
	yq -M 'del(.print_nanny)' ~/.octoprint/config.yaml >  ~/.octoprint/config.yaml

lint: ## check style with flake8
	black print_nanny tests