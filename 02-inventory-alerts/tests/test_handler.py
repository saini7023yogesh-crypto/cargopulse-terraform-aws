import os
import sys

import boto3
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import handler  # noqa: E402

CSV = """sku,product,quantity,reorder_level
LUB-001,Engine Oil 5L,4,10
LUB-002,Gear Oil 1L,50,20
LUB-003,Grease Tube,bad,5
LUB-004,Coolant 4L,10,10
"""


def test_find_low_stock_skips_bad_rows():
    import csv
    import io
    low = handler.find_low_stock(csv.DictReader(io.StringIO(CSV)))
    assert [i["sku"] for i in low] == ["LUB-001", "LUB-004"]


@mock_aws
def test_lambda_publishes_alert():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="stock-bucket")
    s3.put_object(Bucket="stock-bucket", Key="incoming/stock 1.csv", Body=CSV)

    sns = boto3.client("sns")
    topic = sns.create_topic(Name="alerts")["TopicArn"]
    os.environ["TOPIC_ARN"] = topic

    event = {"Records": [{"s3": {"bucket": {"name": "stock-bucket"},
                                  "object": {"key": "incoming/stock+1.csv"}}}]}
    assert handler.lambda_handler(event, None) == {"alerts_sent": 1}


@mock_aws
def test_no_alert_when_stock_ok():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="stock-bucket")
    s3.put_object(Bucket="stock-bucket", Key="incoming/ok.csv",
                  Body="sku,product,quantity,reorder_level\nA,Item,100,10\n")
    os.environ["TOPIC_ARN"] = boto3.client("sns").create_topic(Name="alerts")["TopicArn"]
    event = {"Records": [{"s3": {"bucket": {"name": "stock-bucket"},
                                  "object": {"key": "incoming/ok.csv"}}}]}
    assert handler.lambda_handler(event, None) == {"alerts_sent": 0}
