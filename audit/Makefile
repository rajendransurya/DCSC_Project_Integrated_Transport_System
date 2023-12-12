VERSION=v1
DOCKERUSER="rajendransurya"

build:
	docker build -f Dockerfile -t audit .
push:
	docker tag audit $(DOCKERUSER)/audit:$(VERSION)
	docker push $(DOCKERUSER)/audit:$(VERSION)
	docker tag audit $(DOCKERUSER)/audit:latest
	docker push $(DOCKERUSER)/audit:latest