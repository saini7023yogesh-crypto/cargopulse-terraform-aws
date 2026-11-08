# 02 - Warehouse Inventory Alerts

Upload a stock CSV, get an email if anything is at or below its reorder level.

```
stock.csv -> S3 (incoming/) -> Lambda -> SNS -> Email
```

## Design decisions
- **Event-driven**: no polling, no server; Lambda runs only when a file lands.
- **Prefix + suffix filter** (`incoming/*.csv`): prevents recursive triggers and ignores other files.
- **Malformed rows are skipped**, not fatal: one bad line should not block the whole stock report.
- **Least privilege**: Lambda can read only `incoming/*` and publish to one topic.
- Bucket: public access blocked, encryption on.

## Test (no AWS account needed)
```bash
pip install -r ../requirements-dev.txt
pytest tests/
```

## Deploy
```bash
cd terraform && terraform init
terraform apply -var 'alert_email=you@example.com'
# Confirm the subscription email from AWS, then:
aws s3 cp ../sample-data/stock.csv s3://$(terraform output -raw bucket_name)/incoming/stock.csv
```
You should receive an email listing the low-stock SKUs. `terraform destroy` when done.
