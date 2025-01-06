#!/bin/bash
set -e

# Load environment variables
set -a
source .env
set +a

gcloud functions deploy GoogleFitNotionIntegration \
    --gen2 \
    --runtime python39 \
    --trigger-topic=fit \
    --region=asia-northeast1 \
    --entry-point=handler \
    --timeout=30 \
    --memory=256Mi \
    --set-env-vars=NOTION_SECRET=${NOTION_SECRET},DATABASE_ID=${DATABASE_ID} \
    --source=./src \
    --project=${GCP_PROJECT}
