VERSION=v1
DOCKERUSER="rajendransurya"

build:
	docker build -f Dockerfile -t notification .
push:
	docker tag notification $(DOCKERUSER)/notification:$(VERSION)
	docker push $(DOCKERUSER)/notification:$(VERSION)
	docker tag notification $(DOCKERUSER)/notification:latest
	docker push $(DOCKERUSER)/notification:latest