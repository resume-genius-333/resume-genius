# LiteLLM Deploy GitHub Actions Setup

## Overview
- Workflow file: `.github/workflows/litellm-deploy.yml` builds the LiteLLM image, plans Terraform for the `dev` environment, and applies changes on pushes to `main`.
- The pipeline relies on GitHub OIDC to assume the AWS role `ResumeGeniusGithubActions` (trust defined in `infrastructure/terraform/iam/trust-policy.json`).
- All AWS credentials are provided through repository secrets; no long-lived keys are stored in the repo.

## Required Repository Secrets
| Secret | Purpose |
| --- | --- |
| `AWS_REGION` | AWS region used for Terraform, ECR, and Secrets Manager (e.g. `ap-southeast-1`). |
| `AWS_ROLE_TO_ASSUME` | ARN of the OIDC-enabled IAM role (`arn:aws:iam::084828573819:role/ResumeGeniusGithubActions`). |
| `LITELLM_ECR_REPOSITORY` | Fully qualified ECR repository URI for the LiteLLM image (e.g. `084828573819.dkr.ecr.ap-southeast-1.amazonaws.com/litellm`). |
| `TF_STATE_BUCKET` | S3 bucket name that stores Terraform remote state (must exist before first run). |
| `TF_STATE_LOCK_TABLE` | DynamoDB table name used for Terraform state locking. |
| `LITELLM_DB_MASTER_PASSWORD` | RDS master password injected during Terraform plan/apply. |
| `LITELLM_REDIS_AUTH_TOKEN_SECRET_ARN` | Secrets Manager ARN that stores the Redis AUTH token string. Terraform resolves the secret and applies the token to ElastiCache. |
| `LITELLM_SECRETS_JSON` | JSON map of environment variable names to Secrets Manager / SSM ARNs passed into Terraform (example below). |

Example `LITELLM_SECRETS_JSON` payload (minify before storing if desired):

```json
{
  "DATABASE_URL": "arn:aws:secretsmanager:ap-southeast-1:084828573819:secret:resume-genius/dev/database-url",
  "LITELLM_MASTER_KEY": "arn:aws:secretsmanager:ap-southeast-1:084828573819:secret:resume-genius/dev/litellm-master-key"
}
```

### Redis Auth Token Workflow
1. Generate a strong Redis token (for example `openssl rand -base64 48`).
2. Store the token in AWS Secrets Manager as a plain string secret (e.g. `resume-genius/dev/redis-auth-token`). Avoid wrapping it in JSON so Terraform can use the value directly.
3. Grant the Terraform execution role permission to read that secret (already covered via `litellm_secrets` policy if you reuse the same allow-list).
4. Configure the GitHub Actions secret `LITELLM_REDIS_AUTH_TOKEN_SECRET_ARN` with the ARN of the secret created in step 2. The workflow now passes the ARN to Terraform, which fetches the secret value during plan/apply.

### Enabling HTTPS for LiteLLM
1. Issue or import an ACM certificate in the same AWS region as the load balancer.
2. Populate `alb_https_certificate_arn` (and optionally `alb_redirect_http_to_https`) in `infrastructure/terraform/environments/<env>/terraform.tfvars`.
3. Update any Route53 or external DNS records to alias your custom domain to the ALB DNS name.
4. Re-run the LiteLLM Deploy workflow; Terraform will add an HTTPS listener that terminates TLS with the provided certificate.

## Repository Variables
| Variable | Default | Description |
| --- | --- | --- |
| `TERRAFORM_ENVIRONMENT` | `dev` | Controls the backend key suffix (`resume-genius/litellm/<env>.tfstate`). Override when duplicating the stack. |
| `RDS_MASTER_USERNAME` | `litellm` | Optional override for the database username used in the post-apply secret update step. |
| `RDS_DATABASE_NAME` | `litellm` | Optional override for the database name used in the post-apply secret update step. |

Set variables under **Settings → Secrets and variables → Actions → Variables**.

## GitHub Actions Permissions
- Repository setting **Actions → General → Workflow permissions** must allow the default `Read repository contents`.
- Do **not** disable GitHub OIDC: each job requests `id-token: write` to exchange the identity token for AWS credentials.
- The IAM role must trust `token.actions.githubusercontent.com` with the subject filters defined in `infrastructure/terraform/iam/trust-policy.json`.

## AWS Prerequisites Referenced by the Workflow
- ECR repository that matches `LITELLM_ECR_REPOSITORY`.
- Terraform remote state bucket (`TF_STATE_BUCKET`) and DynamoDB lock table (`TF_STATE_LOCK_TABLE`).
- Secrets in AWS Secrets Manager / Parameter Store whose ARNs are listed in `LITELLM_SECRETS_JSON`.

## Validating the Setup
1. Open **Actions → LiteLLM Deploy → Run workflow** and trigger a dry run using `workflow_dispatch` with an optional `image_tag`.
2. Confirm the jobs obtain temporary AWS credentials (check the `configure-aws-credentials` step output).
3. Inspect the `Terraform Plan` step to ensure the state backend and secret injections succeed.
4. Merge to `main` to let the `terraform-apply` job run and update the `DATABASE_URL` secret automatically.
