#!/bin/bash

# Script to test the webhook endpoint using curl
echo "Testing webhook endpoint with mock payload..."

# Get the path to the mock payload
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PAYLOAD_FILE="$SCRIPT_DIR/mock_payload.json"

# Make the request
curl -X POST \
  -H "Content-Type: application/json" \
  -d @"$PAYLOAD_FILE" \
  http://localhost:8000/api/v1/webhook/mock

echo -e "\nDone!"
