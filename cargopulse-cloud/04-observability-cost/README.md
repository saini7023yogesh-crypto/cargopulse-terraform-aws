# 04 - Observability and Cost Control

Adds monitoring, alerting and a budget on top of project 03.

| Resource | Purpose |
|---|---|
| CloudWatch dashboard | ALB traffic/errors/latency, ECS CPU/memory, RDS CPU/connections in one view |
| 5 alarms | ALB 5xx, unhealthy containers, ECS CPU, RDS CPU, RDS low disk |
| SNS topic + email | Alarm notifications |
| AWS Budget | Email at 80% of actual spend and when forecast exceeds 100% |

## Deploy (after project 03 is applied)
```bash
cd terraform && terraform init
terraform apply \
  -var 'alert_email=you@example.com' \
  -var "ecs_cluster_name=$(terraform -chdir=../../03-three-tier-platform/terraform output -raw ecs_cluster_name)" \
  -var "ecs_service_name=$(terraform -chdir=../../03-three-tier-platform/terraform output -raw ecs_service_name)" \
  -var "alb_arn_suffix=$(terraform -chdir=../../03-three-tier-platform/terraform output -raw alb_arn_suffix)" \
  -var "target_group_arn_suffix=$(terraform -chdir=../../03-three-tier-platform/terraform output -raw target_group_arn_suffix)" \
  -var "db_instance_id=$(terraform -chdir=../../03-three-tier-platform/terraform output -raw db_instance_id)"
```
Confirm the SNS subscription email, then generate traffic and watch the dashboard.

## Why it matters
Well-Architected pillars covered: **Operational Excellence** (dashboard, alarms) and
**Cost Optimization** (budget, right-sized instances, log retention limits).
