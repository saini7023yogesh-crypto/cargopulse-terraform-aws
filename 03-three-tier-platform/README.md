# 03 - Three-Tier Logistics Platform (flagship)

A highly-available web platform on AWS, 100% Terraform.

See the full diagram in [`../docs/architecture.md`](../docs/architecture.md).

```
Internet -> ALB (public subnets) -> ECS Fargate (private app subnets) -> RDS PostgreSQL (private DB subnets)
                                         |
                                         +-> NAT Gateway -> internet (image pulls, updates)
```

## What this demonstrates
| Area | Implementation |
|---|---|
| Networking | VPC, 3 subnet tiers x 2 AZs, IGW, NAT, separate route tables |
| Security | Security-group chaining (ALB -> app -> DB), DB has no internet route, encrypted storage |
| Secrets | RDS-managed password in Secrets Manager, injected into container at start (nothing in code) |
| High availability | 2+ tasks across 2 AZs, ALB health checks, optional Multi-AZ RDS, optional NAT per AZ |
| Scalability | ECS target-tracking auto scaling on CPU (2 to 4 tasks) |
| Reliability | Deployment circuit breaker with automatic rollback |
| Least privilege | Separate ECS execution role (pull image/read one secret) and empty task role |
| CI/CD | GitHub Actions: build image, push to ECR, roll out to ECS |

## API
| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness for the ALB (does not touch the DB, on purpose) |
| `GET /ready` | Readiness (checks the DB) |
| `GET /shipments` / `POST /shipments` | List / create shipments in PostgreSQL |

## Run locally
```bash
docker compose up --build
curl localhost:8000/health
curl -X POST localhost:8000/shipments -H 'content-type: application/json' \
  -d '{"origin":"Sharjah","destination":"Dubai"}'
```

## Deploy to AWS
The ECS service needs an image to exist in ECR, so deploy in two steps:

```bash
cd terraform
terraform init

# 1) create only the registry
terraform apply -target=aws_ecr_repository.app

# 2) build + push the first image
REPO=$(terraform output -raw ecr_repository_url)
REGION=me-central-1
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${REPO%%/*}
docker build -t $REPO:latest ../app
docker push $REPO:latest

# 3) everything else
terraform apply
curl http://$(terraform output -raw alb_dns_name)/health
```
Allow ~10 minutes (RDS creation is the slow part).

### Cost warning
NAT Gateway, ALB and RDS **bill by the hour even when idle**. Take screenshots for your portfolio, then:
```bash
terraform destroy
```

## Choices and trade-offs
| Decision | Why | Production upgrade |
|---|---|---|
| Single NAT gateway | Avoids paying for a second NAT gateway | `single_nat_gateway = false` (NAT per AZ) |
| `db_multi_az = false` | Halves RDS cost for a demo | Set `true` for automatic failover |
| HTTP listener only | No domain/certificate needed for the demo | ACM cert + HTTPS listener + redirect |
| Fargate | No servers/AMIs to patch | EC2 launch type only if cost at scale demands it |
| `skip_final_snapshot` | Clean destroy | Keep final snapshot + deletion protection |
| Local Terraform state | Simple | S3 backend + DynamoDB locking |

## CI/CD setup
Workflow: `.github/workflows/deploy-03.yml`. Create an IAM role that trusts GitHub's OIDC provider
for this repo, give it ECR push + `ecs:UpdateService` permissions, and save its ARN as the repo
secret `AWS_ROLE_ARN`. No long-lived access keys needed.
