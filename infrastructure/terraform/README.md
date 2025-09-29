# LiteLLM on AWS (Terraform)

This Terraform configuration provisions the AWS infrastructure required to run LiteLLM behind an ECS Fargate service with managed PostgreSQL (RDS) and Redis (ElastiCache). The layout is intentionally modular so you can re-use the components for other environments (dev/staging/prod).

## Layout

- `modules/network` – VPC, subnets, routing, optional NAT gateway.
- `modules/rds_postgres` – Encrypted PostgreSQL instance, subnet group, security group rules.
- `modules/elasticache_redis` – Redis replication group with encryption and access control.
- `modules/ecs_litellm` – ECS cluster/service, ALB, IAM roles, CloudWatch logs.
- `environments/dev` – Sample stack wiring the modules together. Duplicate this folder per environment.

## Architecture Overview

The Terraform stack builds a private VPC with public subnets for ingress and private subnets for application and data tiers. The diagram below highlights how traffic and dependencies flow through the environment:

```mermaid
flowchart LR
  Internet((Internet)) --> ALB
  subgraph VPC["VPC (resume-genius-env)"]
    subgraph Public["Public subnets"]
      ALB[Application Load Balancer]
      NAT[NAT Gateway]
    end
    subgraph Private["Private subnets"]
      ECS[ECS Fargate Service<br/>LiteLLM tasks]
      Redis[(ElastiCache Redis)]
      RDS[(RDS PostgreSQL)]
    end
  end
  ALB --> ECS
  ECS --> Redis
  ECS --> RDS
  ECS -->|Fetch secrets| Secrets[(AWS Secrets Manager)]
  ECS -->|Send logs| CloudWatch[(CloudWatch Logs)]
  ECS -->|Pull image| ECR[(Amazon ECR)]
  ECS -->|Outbound API calls| NAT
  NAT --> Internet
```

## Prerequisites

1. **Terraform** `>= 1.6`.
2. **AWS credentials** with permissions to manage VPC, ECS, RDS, ElastiCache, IAM, ALB, CloudWatch.
3. **State backend** – Update `environments/dev/versions.tf` with your S3 bucket and DynamoDB table for locking before the first `terraform init`.
4. **Container image** – The LiteLLM image (with `config.yaml` baked in) must be published to ECR prior to deployment.
5. **Secrets** – Store API keys, LiteLLM master key, database URL, etc. in AWS Secrets Manager or SSM Parameter Store and supply their ARNs via `litellm_secrets`.

## Usage

```bash
# Step 1: Bootstrap remote backend (run once)
cd infrastructure/terraform/bootstrap
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with unique bucket/table names (e.g. resume-genius-tf-state-ap-sg / resume-genius-tf-lock-ap-sg)
terraform init -backend=false
terraform apply

# Step 2: Provision LiteLLM environment (after backend exists)
cd infrastructure/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with real values, secret ARNs, subnets, etc.
terraform init
terraform plan
terraform apply
```

Key variables:

- `availability_zones` – AZs that match your subnets.
- `litellm_container_image` – e.g. `ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/litellm:main`.
- `litellm_secrets` – map of environment variable names to secret ARNs.
- `rds_master_password`, `redis_auth_token_secret_arn` – inject secure values via tfvars or environment variables when planning/applying.
- `alb_https_certificate_arn` – optional ACM certificate for enabling HTTPS at the load balancer.

Outputs include the ALB DNS name, ECS service/cluster identifiers, and datastore endpoints for verification.

## Extending

- Duplicate `environments/dev` for additional stages and adjust the backend key + `environment` variable.
- Attach extra security groups to `additional_*_allowed_security_group_ids` when other services need datastore access.
- Override ECS sizing (`litellm_task_cpu`, `litellm_task_memory`, `litellm_desired_count`) and ALB settings through variables.

> **Security tip:** Avoid committing real secrets. Populate them through Terraform Cloud/Terragrunt variables, or pass with `TF_VAR_` environment variables during workflows.

### Enabling HTTPS

1. Request or import an ACM certificate in the target AWS region (e.g. `ap-southeast-1`).
2. Update your environment `terraform.tfvars` with:
   - `alb_https_certificate_arn = "arn:aws:acm:REGION:ACCOUNT:certificate/ID"`
   - (Optional) `alb_redirect_http_to_https = true` to issue an ALB redirect from port 80 to 443.
3. Ensure the certificate’s domain names point at the ALB’s DNS name via CNAME/ALIAS records.
4. Apply Terraform; it creates an HTTPS listener that terminates TLS with the provided certificate.
