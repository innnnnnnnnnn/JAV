#!/bin/bash

# Configuration
# Default IP from user's history if known, or ask for it
# Based on common OCI patterns:
OCI_USER="ubuntu"
OCI_IP="64.181.254.24" # stockbot IP
SSH_KEY="/Users/innnnnnnnnnnmbp/Downloads/Antigravity/ssh-key-2026-05-04.key"
REMOTE_PATH="/home/ubuntu/JAV"

echo "🚀 Deploying JAV Bot to OCI ($OCI_IP)..."

# Create remote directory and ensure volume files exist
ssh -i $SSH_KEY $OCI_USER@$OCI_IP "mkdir -p $REMOTE_PATH && touch $REMOTE_PATH/torrents.json $REMOTE_PATH/rss_items.json $REMOTE_PATH/pushed_codes.json $REMOTE_PATH/bot.log"

# Copy files (excluding what's in dockerignore)
rsync -avz --exclude-from='.dockerignore' -e "ssh -i $SSH_KEY" ./ $OCI_USER@$OCI_IP:$REMOTE_PATH/

# Copy .env separately (since it's in .dockerignore)
scp -i $SSH_KEY .env $OCI_USER@$OCI_IP:$REMOTE_PATH/.env

# Build and run using docker-compose on remote
echo "📦 Building and starting Docker container on OCI..."
ssh -i $SSH_KEY $OCI_USER@$OCI_IP "cd $REMOTE_PATH && sudo docker compose up -d --build"

echo "✅ Deployment completed!"
echo "🔍 Checking status..."
ssh -i $SSH_KEY $OCI_USER@$OCI_IP "cd $REMOTE_PATH && sudo docker compose ps"
