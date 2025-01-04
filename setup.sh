#!/bin/bash
set -e

# Load environment variables
set -a
source .env
set +a

# Enable required services
gcloud services enable fitness.googleapis.com

# Create PubSub topic if it doesn't exist
if ! gcloud pubsub topics describe fit --project=${GCP_PROJECT} > /dev/null 2>&1; then
  gcloud pubsub topics create fit --project=${GCP_PROJECT}
fi

# Create Cloud Scheduler job
gcloud scheduler jobs create pubsub fit_job \
  --schedule="00 00 * * *" \
  --topic=fit \
  --message-body="go" \
  --time-zone="Asia/Tokyo" \
  --location="asia-northeast1" \
  --project=${GCP_PROJECT}
