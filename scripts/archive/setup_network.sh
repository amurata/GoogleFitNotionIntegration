#!/bin/bash
set -e

# Load environment variables
set -a
source .env
set +a

# Variables
NETWORK_NAME="webhook-network"
SUBNET_NAME="webhook-subnet"
CONNECTOR_NAME="webhook-connector"
ROUTER_NAME="webhook-router"
NAT_NAME="webhook-nat"
REGION="asia-northeast1"
SUBNET_RANGE="10.8.0.0/28"

echo "Setting up network infrastructure for Google Fit Webhook..."

# Create VPC network
echo "Creating VPC network: ${NETWORK_NAME}"
gcloud compute networks create ${NETWORK_NAME} \
    --project=${GCP_PROJECT} \
    --subnet-mode=custom

# Create subnet
echo "Creating subnet: ${SUBNET_NAME}"
gcloud compute networks subnets create ${SUBNET_NAME} \
    --project=${GCP_PROJECT} \
    --network=${NETWORK_NAME} \
    --region=${REGION} \
    --range=${SUBNET_RANGE}

# Create Cloud Router
echo "Creating Cloud Router: ${ROUTER_NAME}"
gcloud compute routers create ${ROUTER_NAME} \
    --project=${GCP_PROJECT} \
    --network=${NETWORK_NAME} \
    --region=${REGION}

# Create Cloud NAT
echo "Creating Cloud NAT: ${NAT_NAME}"
gcloud compute routers nats create ${NAT_NAME} \
    --project=${GCP_PROJECT} \
    --router=${ROUTER_NAME} \
    --region=${REGION} \
    --nat-all-subnet-ip-ranges \
    --auto-allocate-nat-external-ips

# Create VPC Connector
echo "Creating VPC Connector: ${CONNECTOR_NAME}"
gcloud compute networks vpc-access connectors create ${CONNECTOR_NAME} \
    --project=${GCP_PROJECT} \
    --region=${REGION} \
    --network=${NETWORK_NAME} \
    --range=${SUBNET_RANGE} \
    --min-instances=2 \
    --max-instances=3 \
    --machine-type=e2-micro

echo "Network setup completed successfully!"
echo "You can now deploy the webhook function using deploy_webhook.sh"
