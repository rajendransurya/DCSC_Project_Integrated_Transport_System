VERSION=v1
DOCKERUSER="rajendransurya"

build:
	docker build -f Dockerfile -t fare_deduction .
push:
	docker tag fare_deduction $(DOCKERUSER)/fare_deduction:$(VERSION)
	docker push $(DOCKERUSER)/fare_deduction:$(VERSION)
	docker tag fare_deduction $(DOCKERUSER)/fare_deduction:latest
	docker push $(DOCKERUSER)/fare_deduction:latest