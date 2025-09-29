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

# Resolve the Redis AUTH token from Secrets Manager so the sensitive value never needs to
# live in source control. The secret should contain the raw token string (not JSON).
data "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id = var.redis_auth_token_secret_arn
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

# Redis cache used by LiteLLM for session and rate-limiting data. Like the RDS module, we
# rely on a shared implementation to enforce secure defaults.
module "redis" {
  source = "../../modules/elasticache_redis"
  # Prefix name identifies the replication group and all nested resources.
  name = "${var.name_prefix}-${var.environment}-litellm-redis"
  # Attach to the same VPC as the rest of the stack for private networking.
  vpc_id = module.network.vpc_id
  # Private subnets isolate the cache from the public internet.
  subnet_ids = module.network.private_subnet_ids
  # Allow ECS tasks (plus any additional groups) to connect to Redis on its TCP port.
  allowed_security_group_ids = concat([aws_security_group.litellm_internal.id], var.additional_redis_allowed_security_group_ids)
  # Engine and node sizing dictate latency, throughput, and cost characteristics.
  engine_version = var.redis_engine_version
  node_type      = var.redis_node_type
  # When cluster mode is disabled, this is the number of standalone cache nodes.
  num_cache_nodes = var.redis_num_cache_nodes
  # Cluster mode enables sharding for higher scale; toggles below further shape topology.
  cluster_mode_enabled    = var.redis_cluster_mode_enabled
  num_node_groups         = var.redis_num_node_groups
  replicas_per_node_group = var.redis_replicas_per_node_group
  # Automatic failover promotes replicas when primaries fail; Multi-AZ spreads nodes across
  # zones for resilience.
  automatic_failover_enabled = var.redis_automatic_failover_enabled
  multi_az_enabled           = var.redis_multi_az_enabled
  # Encryption settings protect data as it traverses the network and while stored on disk.
  transit_encryption_enabled = var.redis_transit_encryption_enabled
  at_rest_encryption_enabled = var.redis_at_rest_encryption_enabled
  # Optional auth token enforces password-based access; recommended for production.
  auth_token = data.aws_secretsmanager_secret_version.redis_auth_token.secret_string
  # Maintenance/snapshot windows schedule disruptive operations; leave null to let AWS pick
  # defaults or set explicit off-peak times.
  maintenance_window       = var.redis_maintenance_window
  snapshot_window          = var.redis_snapshot_window
  snapshot_retention_limit = var.redis_snapshot_retention_limit
  # Preferred AZs dictate which subnets host cache nodes when multiple are available.
  preferred_cache_cluster_azs = var.redis_preferred_cache_cluster_azs
  # Port defaults to 6379; change only if network policies require it.
  port = var.redis_port
  # Propagate consistent tagging.
  tags = local.tags
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
  subnet_ids        = module.network.private_subnet_ids
  alb_subnet_ids    = module.network.public_subnet_ids
  alb_ingress_cidrs = var.alb_ingress_cidrs
  # Service scaling and sizing knobs control availability and cost.
  desired_count = var.litellm_desired_count
  task_cpu      = var.litellm_task_cpu
  task_memory   = var.litellm_task_memory
  # Assigning a public IP is only needed when private subnets lack NAT or for debugging.
  assign_public_ip = var.litellm_assign_public_ip
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
      # The app needs hostnames for database and cache connections supplied by modules.
      LITELLM_DATABASE_HOST = module.rds.endpoint
      LITELLM_REDIS_HOST    = module.redis.primary_endpoint_address
      # Redis port is numeric, but ECS environment variables must be strings.
      LITELLM_REDIS_PORT = tostring(module.redis.port)
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
