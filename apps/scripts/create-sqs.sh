#!/usr/bin/env bash
set -euo pipefail
REGION="${AWS_REGION:-us-east-1}"
aws sqs create-queue --queue-name concertpass-reservations.fifo   --attributes FifoQueue=true,ContentBasedDeduplication=true,VisibilityTimeout=30   --region "$REGION"
