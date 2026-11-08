# Architecture

## Project 03: Three-tier platform

```mermaid
flowchart TB
    user([User]) --> alb

    subgraph vpc[VPC 10.0.0.0/16 - 2 Availability Zones]
        subgraph pub[Public subnets]
            alb[Application Load Balancer]
            nat[NAT Gateway]
        end
        subgraph app[Private app subnets]
            t1[ECS Fargate task - AZ a]
            t2[ECS Fargate task - AZ b]
        end
        subgraph db[Private DB subnets - no internet route]
            rds[(RDS PostgreSQL)]
        end
    end

    alb --> t1
    alb --> t2
    t1 --> rds
    t2 --> rds
    t1 -. outbound .-> nat
    t2 -. outbound .-> nat
    ecr[(ECR image registry)] -. image pull .-> t1
    sm[Secrets Manager - DB credentials] -. injected at start .-> t1
    cw[CloudWatch Logs, Metrics, Alarms] -. observes .- alb
    cw -. observes .- t1
    cw -. observes .- rds
```

## Project 01: Serverless shipment tracker

```mermaid
flowchart LR
    c([Client]) --> api[API Gateway HTTP API] --> fn[Lambda] --> ddb[(DynamoDB)]
    fn --> logs[CloudWatch Logs]
```

## Project 02: Inventory alerts

```mermaid
flowchart LR
    f[stock.csv] --> s3[(S3 incoming/)] -->|ObjectCreated| fn[Lambda] -->|low stock| sns[SNS] --> mail([Email])
```

## CI/CD

```mermaid
flowchart LR
    dev[git push main] --> gha[GitHub Actions] --> build[docker build] --> ecr[(ECR)] --> ecs[ECS rolling deploy with circuit breaker]
```

## Approximate monthly cost (verify with the AWS Pricing Calculator; prices vary by region)

| Project | Main cost drivers | Rough idea |
|---|---|---|
| 01 Serverless tracker | Lambda, API Gateway, DynamoDB on-demand | Near zero at demo traffic (free tier) |
| 02 Inventory alerts | S3, Lambda, SNS | Near zero |
| 03 Platform | NAT Gateway, ALB, 2 Fargate tasks, RDS | The expensive one: tens of USD/month if left running. **Destroy after demo.** |
| 04 Observability | Dashboard, alarms, logs | A few USD |

## Well-Architected mapping

| Pillar | Where |
|---|---|
| Security | SG chaining, private DB tier, Secrets Manager, least-privilege IAM, encryption, blocked public S3 |
| Reliability | Multi-AZ subnets, ALB health checks, auto scaling, circuit breaker rollback, DynamoDB PITR, RDS backups |
| Performance efficiency | Serverless for spiky load, Fargate right-sizing, HTTP API instead of REST API |
| Cost optimization | On-demand DynamoDB, single NAT option, ECR lifecycle policy, log retention, budget alerts |
| Operational excellence | Terraform for everything, CI/CD, dashboard + alarms |

## Interview talking points
1. "Why is `/health` not checking the database?" A DB outage would make the ALB kill every healthy container and turn a partial outage into a full one. Liveness and readiness are separate endpoints.
2. "Why a separate execution role and task role?" The execution role is for ECS plumbing (pull image, read one secret). The app code gets its own role, which is empty because it needs no AWS API access.
3. "How do you handle secrets?" RDS generates and stores the password in Secrets Manager; ECS injects it at container start. It never appears in code or Terraform variables.
4. "What would you change for production?" HTTPS with ACM, Multi-AZ RDS, NAT per AZ, remote Terraform state, WAF in front of the ALB, final snapshots and deletion protection.
5. "Why serverless for tracking but containers for the platform?" Spiky, simple CRUD fits Lambda; steady traffic with a relational database and longer-running logic fits containers.
