VERSION=v1
DOCKERUSER="rajendransurya"

build:
	docker build -f Dockerfile -t its_gateway .
push:
	docker tag its_gateway $(DOCKERUSER)/its_gateway:$(VERSION)
	docker push $(DOCKERUSER)/its_gateway:$(VERSION)
	docker tag its_gateway $(DOCKERUSER)/its_gateway:latest
	docker push $(DOCKERUSER)/its_gateway:latest