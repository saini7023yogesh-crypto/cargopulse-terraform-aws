# CargoPulse Cloud

Four AWS projects built around one story: **a logistics company moving its operations to the cloud**.
Written by someone who has worked in warehouse and logistics operations, so the scenarios are real,
not "Hello World".

| # | Project | AWS services | Shows |
|---|---|---|---|
| 01 | [Serverless Shipment Tracker](01-serverless-shipment-tracker) | API Gateway, Lambda, DynamoDB | Serverless, event-driven design, least-privilege IAM |
| 02 | [Inventory Alerts](02-inventory-alerts) | S3, Lambda, SNS | Event-driven automation, notifications |
| 03 | [Three-Tier Platform](03-three-tier-platform) | VPC, ALB, ECS Fargate, RDS, ECR, Secrets Manager | Networking, HA, security layers, CI/CD, Docker |
| 04 | [Observability and Cost](04-observability-cost) | CloudWatch, SNS, Budgets | Monitoring, alerting, FinOps |

Everything is provisioned with **Terraform** (Infrastructure as Code).
Diagrams, trade-offs, cost notes and interview talking points: [docs/architecture.md](docs/architecture.md).

## Quick start
```bash
pip install -r requirements-dev.txt

# unit tests (no AWS account needed)
(cd 01-serverless-shipment-tracker && pytest tests -q)
(cd 02-inventory-alerts && pytest tests -q)
(cd 03-three-tier-platform && pip install -r app/requirements.txt && pytest app/tests -q)
```
Each project folder has its own README with deploy steps. Recommended order: 02, 01, 03, then 04.

## Important
- Default region is `me-central-1` (UAE). Change `region` in each `variables.tf` if a service is unavailable there.
- Project 03 costs money while running (NAT Gateway, ALB, RDS). Run `terraform destroy` after you finish.
- Never commit `*.tfstate` or `*.tfvars` (already in `.gitignore`).

## Repo layout
```
01-serverless-shipment-tracker/   src/ tests/ terraform/
02-inventory-alerts/              src/ tests/ terraform/ sample-data/
03-three-tier-platform/           app/ terraform/ docker-compose.yml
04-observability-cost/            terraform/
docs/architecture.md
.github/workflows/                ci.yml, deploy-03.yml
```
