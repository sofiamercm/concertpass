#!/usr/bin/env bash
#destruye la RDS, el security group y los repos de ECR
set -euo pipefail

REGION="us-east-1"
DB_INSTANCE="concertpass-db"
SG_NAME="concertpass-rds-sg"

QUEUE_URL=$(aws sqs get-queue-url --region "$REGION" \
  --queue-name concertpass-reservations.fifo --query QueueUrl --output text)
aws sqs delete-queue --region "$REGION" --queue-url "$QUEUE_URL"

aws rds delete-db-instance --region "$REGION" \
  --db-instance-identifier "$DB_INSTANCE" \
  --skip-final-snapshot --delete-automated-backups

echo "Esperando a que la RDS se elimine..."
aws rds wait db-instance-deleted --region "$REGION" \
  --db-instance-identifier "$DB_INSTANCE"

SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters Name=group-name,Values="$SG_NAME" \
  --query "SecurityGroups[0].GroupId" --output text)
aws ec2 delete-security-group --region "$REGION" --group-id "$SG_ID"

for repo in ticket-api ticket-checkout ticket-worker; do
  aws ecr delete-repository --region "$REGION" \
    --repository-name "$repo" --force
done

echo "Recursos eliminados."
