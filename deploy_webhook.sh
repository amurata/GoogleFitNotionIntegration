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

# Create a security policy for Cloudflare IPs
POLICY_NAME="cloudflare-policy"

# Create the security policy if it doesn't exist
if ! gcloud compute security-policies describe $POLICY_NAME --project=${GCP_PROJECT} &>/dev/null; then
    echo "Creating security policy: $POLICY_NAME"
    gcloud compute security-policies create $POLICY_NAME \
        --project=${GCP_PROJECT}

    # Add Cloudflare IP ranges
    # https://www.cloudflare.com/ips-v4
    CLOUDFLARE_IPS=(
        "173.245.48.0/20"
        "103.21.244.0/22"
        "103.22.200.0/22"
        "103.31.4.0/22"
        "141.101.64.0/18"
        "108.162.192.0/18"
        "190.93.240.0/20"
        "188.114.96.0/20"
        "197.234.240.0/22"
        "198.41.128.0/17"
        "162.158.0.0/15"
        "104.16.0.0/13"
        "104.24.0.0/14"
        "172.64.0.0/13"
        "131.0.72.0/22"
    )

    # Add rules for each Cloudflare IP range
    PRIORITY=1000
    for IP in "${CLOUDFLARE_IPS[@]}"; do
        gcloud compute security-policies rules create $PRIORITY \
            --security-policy=$POLICY_NAME \
            --project=${GCP_PROJECT} \
            --description="Allow Cloudflare IP: $IP" \
            --src-ip-ranges="$IP" \
            --action=allow
        PRIORITY=$((PRIORITY + 1))
    done

    # Add default deny rule
    gcloud compute security-policies rules update 2147483647 \
        --security-policy=$POLICY_NAME \
        --project=${GCP_PROJECT} \
        --description="Default deny rule" \
        --action=deny-403
fi

# Deploy the Cloud Function
gcloud functions deploy GoogleFitWebhook \
    --gen2 \
    --runtime python39 \
    --trigger-http \
    --region=asia-northeast1 \
    --entry-point=webhook_handler \
    --timeout=30 \
    --memory=128Mi \
    --set-env-vars=WEBHOOK_API_KEY=${WEBHOOK_API_KEY},GCP_PROJECT=${GCP_PROJECT} \
    --source=./src \
    --project=${GCP_PROJECT} \
    --allow-unauthenticated \
    --security-policy=$POLICY_NAME

echo "Deployment completed successfully"
echo "Note: Use WEBHOOK_API_KEY for authentication"
echo "Access is restricted to Cloudflare IP ranges using Cloud Armour"
