#!/bin/sh
kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml

kubectl apply -f rfid_service/rfid-deployment.yaml
kubectl apply -f rfid_service/rfid-service.yaml

kubectl apply -f fare_deduction/fare-deduction-deployment.yaml
kubectl apply -f fare_deduction/fare-deduction-service.yaml

kubectl apply -f payments/payment-deployment.yaml
kubectl apply -f payments/payment-service.yaml

kubectl apply -f audit/audit-deployment.yaml

kubectl apply -f logs/logs-deployment.yaml

kubectl apply -f notification/notification-deployment.yaml

kubectl apply -f gateway/gateway-deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
kubectl apply -f gateway/gateway-ingress.yaml
