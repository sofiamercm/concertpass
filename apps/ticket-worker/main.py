import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def poll_once(sqs, queue_url):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=0,
    )
    for message in response.get("Messages", []):
        print("Mensaje recibido:", message["Body"], flush=True)
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        print("Mensaje eliminado:", message["MessageId"], flush=True)


def main():
    sqs = boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    queue_url = os.environ["QUEUE_URL"]
    print("Worker iniciado. Polling cada 5 segundos.", flush=True)
    while True:
        try:
            poll_once(sqs, queue_url)
        except (BotoCoreError, ClientError) as error:
            print("Error SQS:", error, flush=True)
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Worker detenido.", flush=True)
