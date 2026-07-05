build-artifacts:
	./scripts/build_artifacts.sh

pulumi-preview: build-artifacts
	cd infra && pulumi preview

pulumi-up: build-artifacts
	cd infra && pulumi up
