VERSION=v1
DOCKERUSER="rajendransurya"

build:
	docker build -f Dockerfile -t rfid_card .
push:
	docker tag rfid_card $(DOCKERUSER)/rfid_card:$(VERSION)
	docker push $(DOCKERUSER)/rfid_card:$(VERSION)
	docker tag rfid_card $(DOCKERUSER)/rfid_card:latest
	docker push $(DOCKERUSER)/rfid_card:latest