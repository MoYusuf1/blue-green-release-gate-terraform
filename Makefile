TF := terraform -chdir=terraform

.PHONY: init apply destroy test e2e lint check

init: ## Copy the example settings and install providers
	test -f terraform/lab.auto.tfvars.json || cp terraform/lab.auto.tfvars.example.json terraform/lab.auto.tfvars.json
	$(TF) init -input=false

apply: init ## Launch Blue (live) and Green (preview)
	$(TF) apply

destroy: ## Remove everything the lab created
	$(TF) destroy

test: ## Terraform tests (mocked Docker) and script tests; no daemon needed
	$(TF) init -input=false -backend=false
	$(TF) test
	python3 tests/test_scripts.py

e2e: ## The full drill against real containers; cleans up after itself
	./scripts/e2e.sh

lint: ## Formatting and validation
	$(TF) fmt -check -recursive
	$(TF) init -input=false -backend=false
	$(TF) validate

check: lint test ## Everything CI runs except e2e and the external scanners
