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

# Create a temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy source files to temporary directory
cp src/main.py "$TEMP_DIR/main.py"
cp src/util.py "$TEMP_DIR/util.py"
cp src/constants.py "$TEMP_DIR/constants.py"
cp src/requirements.txt "$TEMP_DIR/requirements.txt"

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
    --source="$TEMP_DIR" \
    --project=${GCP_PROJECT} \
    --allow-unauthenticated

# Clean up
rm -rf "$TEMP_DIR"
echo "Cleaned up temporary directory"

echo "Deployment completed successfully"
echo "Note: Use WEBHOOK_API_KEY for authentication"
