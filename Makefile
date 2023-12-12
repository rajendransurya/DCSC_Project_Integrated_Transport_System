VERSION=v1
DOCKERUSER="rajendransurya"

#build and push rfid service
rfidbuild:
	docker build -f rfid_service/Dockerfile -t rfid-card .
rfidpush:
	docker tag rfid-card $(DOCKERUSER)/rfid-card:$(VERSION)
	docker push $(DOCKERUSER)/rfid-card:$(VERSION)
	docker tag rfid-card $(DOCKERUSER)/rfid-card:latest
	docker push $(DOCKERUSER)/rfid-card:latest

#build and push fare deduction service
fdbuild:
	docker build -f fare_deduction/Dockerfile -t fare-deduction .
fdpush:
	docker tag fare-deduction $(DOCKERUSER)/fare-deduction:$(VERSION)
	docker push $(DOCKERUSER)/fare-deduction:$(VERSION)
	docker tag fare-deduction $(DOCKERUSER)/fare-deduction:latest
	docker push $(DOCKERUSER)/fare-deduction:latest

#build and push audit service
auditbuild:
	docker build -f audit/Dockerfile -t audit .
auditpush:
	docker tag audit $(DOCKERUSER)/audit:$(VERSION)
	docker push $(DOCKERUSER)/audit:$(VERSION)
	docker tag audit $(DOCKERUSER)/audit:latest
	docker push $(DOCKERUSER)/audit:latest


#build and push payment service
pmtbuild:
	docker build -f payments/Dockerfile -t payment .
pmtpush:
	docker tag payment $(DOCKERUSER)/payment:$(VERSION)
	docker push $(DOCKERUSER)/payment:$(VERSION)
	docker tag payment $(DOCKERUSER)/payment:latest
	docker push $(DOCKERUSER)/payment:latest

#build and push logging service
logbuild:
	docker build -f logs/Dockerfile -t logs  .

logpush:
	docker tag logs  $(DOCKERUSER)/its-logs:$(VERSION)
	docker push $(DOCKERUSER)/its-logs:$(VERSION)
	docker tag logs  $(DOCKERUSER)/its-logs:latest
	docker push $(DOCKERUSER)/its-logs:latest

#build and push notification service
nfbuild:
	docker build -f notification/Dockerfile -t notification .
nfpush:
	docker tag notification $(DOCKERUSER)/notification:$(VERSION)
	docker push $(DOCKERUSER)/notification:$(VERSION)
	docker tag notification $(DOCKERUSER)/notification:latest
	docker push $(DOCKERUSER)/notification:latest

gwbuild:
	docker build -f gateway/Dockerfile -t its-gateway .
gwpush:
	docker tag its-gateway $(DOCKERUSER)/its-gateway:$(VERSION)
	docker push $(DOCKERUSER)/its-gateway:$(VERSION)
	docker tag its-gateway $(DOCKERUSER)/its-gateway:latest
	docker push $(DOCKERUSER)/its-gateway:latest





