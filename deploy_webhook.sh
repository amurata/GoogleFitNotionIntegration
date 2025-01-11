#!/bin/bash
set -e

# Load environment variables
set -a
source .env
set +a

# Generate a random API key if not exists
if [ -z "$WEBHOOK_API_KEY" ]; then
    WEBHOOK_API_KEY=$(openssl rand -hex 32)
    echo "WEBHOOK_API_KEY=$WEBHOOK_API_KEY" >> .env
    echo "Generated new WEBHOOK_API_KEY"
fi

# Deploy the Cloud Function
echo "Deploying Cloud Function..."
gcloud functions deploy GoogleFitWebhook \
    --gen2 \
    --runtime python39 \
    --trigger-http \
    --region=asia-northeast1 \
    --entry-point=webhook_handler \
    --timeout=540 \
    --memory=256Mi \
    --min-instances=1 \
    --set-env-vars=WEBHOOK_API_KEY=${WEBHOOK_API_KEY},GCP_PROJECT=${GCP_PROJECT} \
    --source=./src \
    --project=${GCP_PROJECT} \
    --allow-unauthenticated

echo "Deployment completed successfully"
echo "Note: Use WEBHOOK_API_KEY for authentication"
