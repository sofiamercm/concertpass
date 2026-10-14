import json
import os
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

REQUIRED_FIELDS = ["concert_id", "user_id", "ticket_type", "quantity"]


def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id  UUID PRIMARY KEY,
            concert_id      VARCHAR   NOT NULL,
            user_id         VARCHAR   NOT NULL,
            ticket_type     VARCHAR   NOT NULL,
            quantity        INTEGER   NOT NULL,
            status          VARCHAR   NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
        """
    )
    connection.commit()
    cursor.close()
    connection.close()


@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object"}), 400

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        return jsonify({"error": "Missing fields: " + ", ".join(missing)}), 400

    if not isinstance(data["concert_id"], str) or not data["concert_id"].strip():
        return jsonify({"error": "concert_id must be a nonempty string"}), 400

    reservation_id = str(uuid.uuid4())
    now = datetime.utcnow()

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO reservations
            (reservation_id, concert_id, user_id, ticket_type, quantity,
             status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reservation_id,
                data["concert_id"],
                data["user_id"],
                data["ticket_type"],
                data["quantity"],
                "pending",
                now,
                now,
            ),
        )
        connection.commit()
        cursor.close()
        connection.close()
    except psycopg2.Error as error:
        return jsonify({"error": "Database error", "detail": str(error)}), 500

    try:
        sqs = boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        sqs.send_message(
            QueueUrl=os.environ["QUEUE_URL"],
            MessageBody=json.dumps(data),
            MessageGroupId=data["concert_id"],
            MessageDeduplicationId=reservation_id,
        )
    except (BotoCoreError, ClientError):
        app.logger.exception("Could not enqueue reservation %s", reservation_id)
        return jsonify({
            "error": "Reservation saved but enqueue failed",
            "reservation_id": reservation_id,
            "status": "pending",
        }), 503

    return jsonify({
        "message": "Reservation pending",
        "status": "pending",
        "reservation_id": reservation_id,
    }), 202


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
