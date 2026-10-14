#!/usr/bin/env bash
#Crear el security group, abre el 5432 a tu IP y levanta Postgres
set -euo pipefail

REGION="us-east-1"
DB_INSTANCE="concertpass-db"
DB_NAME="concertpass"
DB_USER="postgres"
DB_PASSWORD="${DB_PASSWORD:?Define DB_PASSWORD antes de correr el script}"
SG_NAME="concertpass-rds-sg"

VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" \
  --filters Name=isDefault,Values=true \
  --query "Vpcs[0].VpcId" --output text)

SG_ID=$(aws ec2 create-security-group --region "$REGION" \
  --group-name "$SG_NAME" \
  --description "ConcertPass RDS access" \
  --vpc-id "$VPC_ID" \
  --query GroupId --output text)

MY_IP=$(curl -s https://checkip.amazonaws.com)

aws ec2 authorize-security-group-ingress --region "$REGION" \
  --group-id "$SG_ID" --protocol tcp --port 5432 --cidr "${MY_IP}/32"

aws rds create-db-instance --region "$REGION" \
  --db-instance-identifier "$DB_INSTANCE" \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 20 \
  --db-name "$DB_NAME" \
  --master-username "$DB_USER" \
  --master-user-password "$DB_PASSWORD" \
  --vpc-security-group-ids "$SG_ID" \
  --publicly-accessible \
  --backup-retention-period 0

echo "Esperando a que la RDS este disponible (varios minutos)..."
aws rds wait db-instance-available --region "$REGION" \
  --db-instance-identifier "$DB_INSTANCE"

ENDPOINT=$(aws rds describe-db-instances --region "$REGION" \
  --db-instance-identifier "$DB_INSTANCE" \
  --query "DBInstances[0].Endpoint.Address" --output text)

echo "RDS lista. DB_HOST=$ENDPOINT"