"""CargoPulse shipment tracker: API Gateway (HTTP API) -> Lambda -> DynamoDB."""
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

STATUSES = ["CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"]
_table = None


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def now():
    return datetime.now(timezone.utc).isoformat()


def response(code, body):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def create_shipment(event):
    try:
        data = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Body must be valid JSON"})

    missing = [f for f in ("origin", "destination") if not data.get(f)]
    if missing:
        return response(400, {"error": f"Missing fields: {', '.join(missing)}"})

    item = {
        "shipment_id": "CP-" + uuid.uuid4().hex[:8].upper(),
        "origin": data["origin"],
        "destination": data["destination"],
        "customer": data.get("customer", "unknown"),
        "status": "CREATED",
        "created_at": now(),
        "history": [{"status": "CREATED", "at": now()}],
    }
    table().put_item(Item=item)
    return response(201, item)


def get_shipment(shipment_id):
    item = table().get_item(Key={"shipment_id": shipment_id}).get("Item")
    if not item:
        return response(404, {"error": "Shipment not found"})
    return response(200, item)


def update_status(shipment_id, event):
    try:
        new_status = json.loads(event.get("body") or "{}").get("status")
    except json.JSONDecodeError:
        return response(400, {"error": "Body must be valid JSON"})

    if new_status not in STATUSES:
        return response(400, {"error": f"status must be one of {STATUSES}"})

    item = table().get_item(Key={"shipment_id": shipment_id}).get("Item")
    if not item:
        return response(404, {"error": "Shipment not found"})

    # Business rule: a shipment can only move forward in its lifecycle
    if STATUSES.index(new_status) <= STATUSES.index(item["status"]):
        return response(409, {"error": f"Cannot move from {item['status']} to {new_status}"})

    try:
        result = table().update_item(
            Key={"shipment_id": shipment_id},
            UpdateExpression="SET #s = :s, history = list_append(history, :h)",
            ConditionExpression="attribute_exists(shipment_id) AND #s = :current",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": new_status,
                ":current": item["status"],
                ":h": [{"status": new_status, "at": now()}],
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as err:
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(409, {"error": "Shipment was updated concurrently, retry"})
        raise
    return response(200, result["Attributes"])


def lambda_handler(event, context):
    route = event.get("routeKey", "")
    shipment_id = (event.get("pathParameters") or {}).get("id")

    if route == "POST /shipments":
        return create_shipment(event)
    if route == "GET /shipments/{id}":
        return get_shipment(shipment_id)
    if route == "PATCH /shipments/{id}/status":
        return update_status(shipment_id, event)
    return response(404, {"error": "Route not found"})
