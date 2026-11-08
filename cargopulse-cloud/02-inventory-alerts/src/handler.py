"""CargoPulse inventory alerts: S3 upload (CSV) -> Lambda -> SNS email for low stock."""
import csv
import io
import os
from urllib.parse import unquote_plus

import boto3


def find_low_stock(rows):
    low = []
    for row in rows:
        try:
            qty = int(row["quantity"])
            reorder = int(row["reorder_level"])
        except (KeyError, ValueError, TypeError):
            continue  # skip malformed rows instead of failing the whole file
        if qty <= reorder:
            low.append({"sku": row.get("sku", "?"), "product": row.get("product", "?"),
                        "quantity": qty, "reorder_level": reorder})
    return low


def build_message(key, low):
    lines = [f"Low stock detected in file: {key}", ""]
    for item in low:
        lines.append(
            f"- {item['sku']} | {item['product']}: {item['quantity']} left "
            f"(reorder at {item['reorder_level']})"
        )
    return "\n".join(lines)


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    sns = boto3.client("sns")
    topic_arn = os.environ["TOPIC_ARN"]
    alerts_sent = 0

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        low = find_low_stock(csv.DictReader(io.StringIO(body)))

        if low:
            sns.publish(
                TopicArn=topic_arn,
                Subject=f"[CargoPulse] {len(low)} item(s) low on stock",
                Message=build_message(key, low),
            )
            alerts_sent += 1

    return {"alerts_sent": alerts_sent}
