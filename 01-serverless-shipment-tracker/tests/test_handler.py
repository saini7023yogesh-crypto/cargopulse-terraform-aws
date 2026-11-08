import json
import os
import sys

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ["TABLE_NAME"] = "shipments-test"

import handler  # noqa: E402


@pytest.fixture(autouse=True)
def dynamodb():
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="shipments-test",
            KeySchema=[{"AttributeName": "shipment_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "shipment_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        handler._table = None
        yield


def call(route, body=None, shipment_id=None):
    event = {"routeKey": route, "pathParameters": {"id": shipment_id} if shipment_id else None}
    if body is not None:
        event["body"] = json.dumps(body)
    res = handler.lambda_handler(event, None)
    return res["statusCode"], json.loads(res["body"])


def create():
    return call("POST /shipments", {"origin": "Sharjah", "destination": "Dubai"})[1]["shipment_id"]


def test_create_and_get():
    code, body = call("POST /shipments", {"origin": "Sharjah", "destination": "Dubai"})
    assert code == 201 and body["status"] == "CREATED"
    code, fetched = call("GET /shipments/{id}", shipment_id=body["shipment_id"])
    assert code == 200 and fetched["origin"] == "Sharjah"


def test_create_requires_fields():
    code, _ = call("POST /shipments", {"origin": "Sharjah"})
    assert code == 400


def test_get_missing_is_404():
    assert call("GET /shipments/{id}", shipment_id="CP-NOPE")[0] == 404


def test_status_moves_forward_and_records_history():
    sid = create()
    code, body = call("PATCH /shipments/{id}/status", {"status": "IN_TRANSIT"}, sid)
    assert code == 200 and body["status"] == "IN_TRANSIT"
    assert [h["status"] for h in body["history"]] == ["CREATED", "IN_TRANSIT"]


def test_status_cannot_go_backwards():
    sid = create()
    call("PATCH /shipments/{id}/status", {"status": "DELIVERED"}, sid)
    assert call("PATCH /shipments/{id}/status", {"status": "IN_TRANSIT"}, sid)[0] == 409


def test_invalid_status_rejected():
    sid = create()
    assert call("PATCH /shipments/{id}/status", {"status": "LOST"}, sid)[0] == 400
