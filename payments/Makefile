VERSION=v1
DOCKERUSER="rajendransurya"

build:
	docker build -f Dockerfile -t payment .
push:
	docker tag payment $(DOCKERUSER)/payment:$(VERSION)
	docker push $(DOCKERUSER)/payment:$(VERSION)
	docker tag payment $(DOCKERUSER)/payment:latest
	docker push $(DOCKERUSER)/payment:latest