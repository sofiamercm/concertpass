import os

import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )


@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.get_json()

    concert_id = data["concert_id"]
    user_id = data["user_id"]
    ticket_type = data["ticket_type"]
    quantity = data["quantity"]

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reservations
        (concert_id, user_id, ticket_type, quantity, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            concert_id,
            user_id,
            ticket_type,
            quantity,
            "confirmed"
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "message": "Reservation confirmed"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)