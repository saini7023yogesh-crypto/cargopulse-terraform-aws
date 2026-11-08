# 01 - Serverless Shipment Tracker

Track shipments through their lifecycle with **zero servers**.

```
Client -> API Gateway (HTTP API) -> Lambda -> DynamoDB
```

| Endpoint | Purpose |
|---|---|
| `POST /shipments` | Create shipment (`origin`, `destination`, optional `customer`) |
| `GET /shipments/{id}` | Get status + full history |
| `PATCH /shipments/{id}/status` | Move to next status (cannot go backwards) |

Lifecycle: `CREATED -> PICKED_UP -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED`

## Design decisions
- **DynamoDB on-demand**: unpredictable traffic, pay per request, no capacity planning.
- **HTTP API (not REST API)**: cheaper and lower latency; no need for API keys/usage plans here.
- **Least-privilege IAM**: Lambda gets only `PutItem/GetItem/UpdateItem` on one table.
- **Conditional write**: `UpdateItem` checks the old status, so two concurrent updates cannot corrupt history.
- **Business rule in code**: status can only move forward (HTTP 409 otherwise).

## Test (no AWS account needed)
```bash
pip install -r ../requirements-dev.txt
pytest tests/
```

## Deploy
```bash
cd terraform && terraform init && terraform apply
API=$(terraform output -raw api_url)

curl -X POST $API/shipments -H 'content-type: application/json' \
  -d '{"origin":"Sharjah","destination":"Dubai","customer":"ACME"}'
curl $API/shipments/CP-XXXXXXXX
curl -X PATCH $API/shipments/CP-XXXXXXXX/status -d '{"status":"IN_TRANSIT"}'
```
Destroy when done: `terraform destroy`.
