// Main environment wiring for deploying LiteLLM in AWS. This file stitches together
// networking, persistent data stores, and the ECS service that runs the application.

# Local helpers that keep repeated expressions readable and ensure downstream modules
# receive their inputs in the formats they expect.
locals {
  # Start with caller-provided tags and augment them with consistent identifiers so
  # every resource is labeled with its environment and application.
  tags = merge(var.tags, {
    Environment = var.environment
    Application = "litellm"
  })

  # Transform the secret map (ENV_VAR => ARN) into the list-of-objects format the ECS
  # module consumes when configuring task definitions.
  litellm_secret_list = [for name, arn in var.litellm_secrets : {
    name       = name
    value_from = arn
  }]

  # Collect the unique set of secret ARNs so IAM policies can grant access without
  # duplicates that would bloat the policy document.
  litellm_secret_arns = distinct(values(var.litellm_secrets))

  backend_db_bastion_name = "${var.name_prefix}-${var.environment}-db-bastion"
}

# Provision the VPC, subnets, and routing needed by all other stacks. Centralising this
# logic in the network module keeps the environment definitions concise.
module "network" {
  # Reuse the shared module so each environment gets identical network primitives.
  source = "../../modules/network"
  # Prefix all network resource names with the project and environment (e.g. dev) so we
  # can distinguish them in the AWS console.
  name_prefix = "${var.name_prefix}-${var.environment}"
  # Base IPv4 CIDR for the VPC. Changing this later requires replacement of the VPC, so
  # pick an address space that will not conflict with on-prem or other clouds.
  vpc_cidr = var.vpc_cidr
  # Public subnets host shared entry points like load balancers; they receive public IPs.
  public_subnet_cidrs = var.public_subnet_cidrs
  # Private subnets keep compute and databases isolated from the internet.
  private_subnet_cidrs = var.private_subnet_cidrs
  # Availability zones spread subnets for resiliency; ensure the list matches the CIDR
  # counts so each subnet lands in an AZ that actually exists in the region.
  availability_zones = var.availability_zones
  # NAT gateways let private subnets reach the internet for patching without exposing
  # instances publicly. Turning this off saves cost but breaks outbound connectivity.
  enable_nat = var.enable_nat_gateway
  # Apply consistent tagging so the network resources inherit the environment metadata.
  tags = local.tags
}

# Shared security group that allows east-west traffic between LiteLLM components such as
# the ECS service, Redis, and Postgres. Outbound is fully open because AWS SGs are
# stateful and we only rely on other groups to restrict inbound traffic.
resource "aws_security_group" "litellm_internal" {
  # Human-readable name that appears in the console and encodes environment context.
  name = "${var.name_prefix}-${var.environment}-internal"
  # Document the intent for future operators looking at the resource in AWS.
  description = "Security group shared by LiteLLM tasks for data plane access"
  # Associate the security group with the VPC created by the network module.
  vpc_id = module.network.vpc_id

  # Allow any outbound traffic so tasks can reach external services, updates, or AWS APIs.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tagging aids filtering and billing in the AWS console.
  tags = merge(local.tags, {
    Name = "${var.name_prefix}-${var.environment}-internal"
  })
}

# Dedicated security group for the Resume Genius backend service. The backend ECS tasks (or
# other compute) will attach to this group so the database can grant it ingress without
# exposing Postgres more broadly.
resource "aws_security_group" "backend_internal" {
  name        = "${var.name_prefix}-${var.environment}-backend"
  description = "Security group shared by Resume Genius backend components"
  vpc_id      = module.network.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${var.name_prefix}-${var.environment}-backend"
  })
}

resource "aws_security_group" "backend_db_bastion" {
  count       = var.backend_db_bastion_enabled ? 1 : 0
  name        = "${local.backend_db_bastion_name}-sg"
  description = "Bastion host security group for backend database access"
  vpc_id      = module.network.vpc_id

  dynamic "ingress" {
    for_each = var.backend_db_bastion_ingress_cidrs
    content {
      description = "SSH access"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.backend_db_bastion_name}-sg"
    Role = "db-bastion"
  })
}

data "aws_ssm_parameter" "backend_db_bastion_ami" {
  count = var.backend_db_bastion_enabled ? 1 : 0
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-arm64"
}

resource "aws_iam_role" "backend_db_bastion" {
  count = var.backend_db_bastion_enabled ? 1 : 0
  name  = "${local.backend_db_bastion_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
  tags = merge(local.tags, {
    Name = "${local.backend_db_bastion_name}-role"
  })
}

resource "aws_iam_role_policy_attachment" "backend_db_bastion_ssm" {
  count      = var.backend_db_bastion_enabled ? 1 : 0
  role       = aws_iam_role.backend_db_bastion[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_service_linked_role" "ssm" {
  count            = var.backend_db_bastion_enabled ? 1 : 0
  aws_service_name = "ssm.amazonaws.com"
  description      = "Enables AWS Systems Manager access for resume-genius bastion instances"
}

resource "aws_iam_instance_profile" "backend_db_bastion" {
  count = var.backend_db_bastion_enabled ? 1 : 0
  name  = "${local.backend_db_bastion_name}-profile"
  role  = aws_iam_role.backend_db_bastion[0].name
  tags  = local.tags
}

resource "aws_instance" "backend_db_bastion" {
  count = var.backend_db_bastion_enabled ? 1 : 0

  ami                         = data.aws_ssm_parameter.backend_db_bastion_ami[0].value
  instance_type               = var.backend_db_bastion_instance_type
  subnet_id                   = module.network.public_subnet_ids[0]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.backend_db_bastion[0].name
  vpc_security_group_ids = compact([
    aws_security_group.backend_db_bastion[0].id
  ])
  key_name = var.backend_db_bastion_key_name

  root_block_device {
    volume_size = var.backend_db_bastion_root_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  tags = merge(local.tags, {
    Name = local.backend_db_bastion_name
    Role = "db-bastion"
  })
}

# Managed PostgreSQL database that stores LiteLLM metadata. Using the reusable module
# keeps security-group plumbing and encryption settings consistent across environments.
module "rds" {
  source = "../../modules/rds_postgres"
  # Unique identifier for the RDS resources; names include environment for clarity.
  name = "${var.name_prefix}-${var.environment}-litellm-db"
  # Attach the database to the VPC so it is reachable only inside our network.
  vpc_id = module.network.vpc_id
  # Private subnets ensure the database never exposes a public IP address.
  subnet_ids = module.network.private_subnet_ids
  # Permit ECS tasks (and any extra groups) to connect on the database port.
  allowed_security_group_ids = concat([aws_security_group.litellm_internal.id], var.additional_rds_allowed_security_group_ids)
  # Postgres engine version; upgrades may require downtime so keep consistent across envs.
  engine_version = var.rds_engine_version
  # Instance class determines CPU/RAM; match to workload demand to balance cost.
  instance_class = var.rds_instance_class
  # Administrative credentials that Terraform sets when the instance is created.
  username = var.rds_master_username
  password = var.rds_master_password
  # Initial database created for LiteLLM to use; app must manage schema migrations.
  db_name = var.rds_database_name
  # Storage allocations control the baseline IO and capacity; scaling up may cause short
  # outages, so size generously.
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  # Storage type affects performance and price (gp3 is general purpose SSD).
  storage_type      = var.rds_storage_type
  storage_encrypted = var.rds_storage_encrypted
  # Optional customer-managed KMS key for encryption; null falls back to AWS-managed key.
  kms_key_id = var.rds_kms_key_id
  # Multi-AZ adds an automatic standby in another AZ for higher availability at higher cost.
  multi_az = var.rds_multi_az
  # Retention controls how many days of automated backups Amazon keeps for point-in-time
  # restores; increase for stricter recovery objectives.
  backup_retention_period = var.rds_backup_retention_period
  # Skipping the final snapshot speeds destroy operations but risks irreversible data loss.
  skip_final_snapshot = var.rds_skip_final_snapshot
  # Apply modifications immediately (true) trades safety for speed; use false to queue
  # changes for the next maintenance window in production.
  apply_immediately = var.rds_apply_immediately
  # Deletion protection prevents accidental `terraform destroy` from wiping prod data.
  deletion_protection = var.rds_deletion_protection
  # Performance Insights collects database metrics; incurs cost but aids troubleshooting.
  performance_insights_enabled    = var.rds_performance_insights_enabled
  performance_insights_kms_key_id = var.rds_performance_insights_kms_key_id
  # Pass environment-aware tags for governance.
  tags = local.tags
}

# Generate unique credentials for the backend database so Terraform never needs a hardcoded
# password. The resulting secret is stored in AWS Secrets Manager for the application to read.
resource "random_password" "backend_rds_master" {
  count   = var.backend_rds_enabled ? 1 : 0
  length  = 24
  special = false
}

# Managed PostgreSQL instance dedicated to the FastAPI backend. Sized for dev workloads and
# isolated from the LiteLLM database so each service can evolve independently.
module "backend_rds" {
  count  = var.backend_rds_enabled ? 1 : 0
  source = "../../modules/rds_postgres"

  name   = "${var.name_prefix}-${var.environment}-backend-db"
  vpc_id = module.network.vpc_id

  subnet_ids = module.network.private_subnet_ids

  allowed_security_group_ids = concat([
    aws_security_group.backend_internal.id,
    aws_security_group.litellm_internal.id
  ], var.additional_backend_rds_allowed_security_group_ids)

  engine_version                  = var.backend_rds_engine_version
  instance_class                  = var.backend_rds_instance_class
  username                        = var.backend_rds_master_username
  password                        = random_password.backend_rds_master[0].result
  db_name                         = var.backend_rds_database_name
  allocated_storage               = var.backend_rds_allocated_storage
  max_allocated_storage           = var.backend_rds_max_allocated_storage
  storage_type                    = var.backend_rds_storage_type
  storage_encrypted               = var.backend_rds_storage_encrypted
  kms_key_id                      = var.backend_rds_kms_key_id
  multi_az                        = var.backend_rds_multi_az
  backup_retention_period         = var.backend_rds_backup_retention_period
  skip_final_snapshot             = var.backend_rds_skip_final_snapshot
  apply_immediately               = var.backend_rds_apply_immediately
  deletion_protection             = var.backend_rds_deletion_protection
  performance_insights_enabled    = var.backend_rds_performance_insights_enabled
  performance_insights_kms_key_id = var.backend_rds_performance_insights_kms_key_id
  tags                            = local.tags
}

locals {
  # Prefer a friendly hostname for clients when one is supplied; otherwise fall back to
  # the native RDS endpoint. Keeping this local centralizes how we reference the database
  # host across secrets and outputs.
  backend_rds_hostname = var.backend_rds_enabled ? coalesce(var.backend_rds_custom_hostname, module.backend_rds[0].endpoint) : null
  backend_rds_endpoint = var.backend_rds_enabled ? module.backend_rds[0].endpoint : null
  backend_rds_port     = var.backend_rds_enabled ? module.backend_rds[0].port : null
}

# Optionally publish a custom DNS record in Route 53 to point the friendly hostname at the
# RDS endpoint. This is gated behind variables so environments without hosted zones skip it.
data "aws_route53_zone" "backend_rds" {
  count        = var.backend_rds_dns_zone_name == null ? 0 : 1
  name         = var.backend_rds_dns_zone_name
  private_zone = var.backend_rds_dns_zone_private
}

resource "aws_route53_record" "backend_rds" {
  count           = var.backend_rds_enabled && var.backend_rds_dns_zone_name != null && var.backend_rds_dns_record_name != null ? 1 : 0
  zone_id         = data.aws_route53_zone.backend_rds[0].zone_id
  name            = var.backend_rds_dns_record_name
  type            = "CNAME"
  ttl             = var.backend_rds_dns_record_ttl
  allow_overwrite = true
  records         = [local.backend_rds_endpoint]
}

# Secret that stores the backend connection details in JSON form. Both local development and
# deployed services can reference this ARN to fetch credentials without baking them into
# environment variables or Terraform state outputs.
resource "aws_secretsmanager_secret" "backend_db" {
  count       = var.backend_rds_enabled ? 1 : 0
  name        = var.backend_rds_secret_name
  description = "Resume Genius backend database credentials"
  tags        = local.tags
}

resource "aws_secretsmanager_secret_version" "backend_db" {
  count     = var.backend_rds_enabled ? 1 : 0
  secret_id = aws_secretsmanager_secret.backend_db[0].id
  secret_string = jsonencode({
    engine   = "postgresql"
    host     = local.backend_rds_hostname
    aws_host = local.backend_rds_endpoint
    port     = local.backend_rds_port
    username = var.backend_rds_master_username
    password = random_password.backend_rds_master[0].result
    dbname   = var.backend_rds_database_name
    url      = "postgresql://${var.backend_rds_master_username}:${random_password.backend_rds_master[0].result}@${local.backend_rds_hostname}/${var.backend_rds_database_name}"
  })
}

# S3 bucket used by LiteLLM for response caching so we avoid keeping a Redis cluster
# running around the clock. A random suffix keeps the bucket name globally unique.
resource "random_id" "litellm_cache_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "litellm_cache" {
  bucket = lower("${var.name_prefix}-${var.environment}-litellm-cache-${random_id.litellm_cache_suffix.hex}")
  tags   = local.tags
}

# Block any form of public access on the cache bucket since it only needs to serve ECS tasks.
resource "aws_s3_bucket_public_access_block" "litellm_cache" {
  bucket                  = aws_s3_bucket.litellm_cache.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enforce server-side encryption so cached responses are protected at rest.
resource "aws_s3_bucket_server_side_encryption_configuration" "litellm_cache" {
  bucket = aws_s3_bucket.litellm_cache.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ECS Fargate service that runs the LiteLLM container behind an Application Load Balancer.
# The module encapsulates IAM roles, networking, and observability setup.
module "litellm" {
  source = "../../modules/ecs_litellm"
  # Prefix keeps the ECS cluster, service, and ALB names aligned with the environment.
  name_prefix = "${var.name_prefix}-${var.environment}-litellm"
  # Region informs CloudWatch logging configuration inside the module.
  aws_region = var.aws_region
  # Container settings describe which image to run and how to start it.
  container_image   = var.litellm_container_image
  container_command = var.litellm_container_command
  container_port    = var.litellm_container_port
  # Networking parameters tie the service and load balancer to our VPC layout.
  vpc_id            = module.network.vpc_id
  subnet_ids        = var.litellm_assign_public_ip ? module.network.public_subnet_ids : module.network.private_subnet_ids
  alb_subnet_ids    = module.network.public_subnet_ids
  alb_ingress_cidrs = var.alb_ingress_cidrs
  # Service scaling and sizing knobs control availability and cost.
  desired_count = var.litellm_desired_count
  task_cpu      = var.litellm_task_cpu
  task_memory   = var.litellm_task_memory
  # Assigning a public IP is only needed when private subnets lack NAT or for debugging.
  assign_public_ip       = var.litellm_assign_public_ip
  enable_execute_command = var.litellm_enable_execute_command
  # Attach the shared internal security group plus any caller-specified ones (e.g. to allow
  # observability agents to reach the tasks).
  additional_service_security_groups = concat([aws_security_group.litellm_internal.id], var.additional_service_security_group_ids)
  # Combine required environment variables (database/cache connectivity) with caller extras.
  environment = merge(
    {
      # Pass region for SDKs that default to the task's metadata service region.
      AWS_REGION = var.aws_region
      # LiteLLM reads config from this path inside the container image.
      LITELLM_CONFIG_PATH = var.litellm_config_path
      # The app needs hostnames for database connections supplied by modules.
      LITELLM_DATABASE_HOST = module.rds.endpoint
      # Configure LiteLLM cache integration to use the dedicated S3 bucket instead of Redis.
      LITELLM_CACHE_TYPE      = "s3"
      LITELLM_CACHE_S3_BUCKET = aws_s3_bucket.litellm_cache.bucket
      LITELLM_CACHE_S3_REGION = var.aws_region
    },
    var.litellm_environment
  )
  # Secrets are injected into the task as environment variables using SSM or Secrets Manager.
  secrets     = local.litellm_secret_list
  secret_arns = local.litellm_secret_arns
  # Health check path controls how the target group tests container responsiveness.
  health_check_path = var.litellm_health_check_path
  # Load balancer listener and protection settings influence external access and safety.
  listener_port           = var.alb_listener_port
  https_listener_port     = var.alb_https_listener_port
  https_certificate_arn   = var.alb_https_certificate_arn
  https_ssl_policy        = var.alb_https_ssl_policy
  redirect_http_to_https  = var.alb_redirect_http_to_https
  alb_deletion_protection = var.alb_deletion_protection
  # Control log retention in CloudWatch; longer periods improve auditing but cost more.
  log_retention_days = var.litellm_log_retention_days
  # Apply consistent tagging to every resource the module generates.
  tags = local.tags
}

# Allow the LiteLLM ECS task role to read and write cached responses in the dedicated S3 bucket.
data "aws_iam_role" "litellm_task" {
  name = module.litellm.task_role_name
}

resource "aws_iam_role_policy" "litellm_cache_s3" {
  name = "${var.name_prefix}-${var.environment}-litellm-cache-s3"
  role = data.aws_iam_role.litellm_task.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [aws_s3_bucket.litellm_cache.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = ["${aws_s3_bucket.litellm_cache.arn}/*"]
      }
    ]
  })
}
