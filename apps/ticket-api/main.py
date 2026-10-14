import os
import uuid
from datetime import datetime

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

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        return jsonify({"error": "Missing fields: " + ", ".join(missing)}), 400

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
                "confirmed",
                now,
                now,
            ),
        )
        connection.commit()
        cursor.close()
        connection.close()
    except psycopg2.Error as error:
        return jsonify({"error": "Database error", "detail": str(error)}), 500

    return jsonify({
        "message": "Reservation confirmed",
        "reservation_id": reservation_id,
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)