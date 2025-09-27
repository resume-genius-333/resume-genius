# Controls the AWS region where AWS resources are provisioned. Switching regions creates
# entirely new infrastructure in that geography, so keep values consistent per environment.
variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
}

# Human-readable label (e.g. dev, staging, prod) that the configuration uses for tagging
# and naming. Changing this influences resource names; pick a stable value per stage.
variable "environment" {
  type        = string
  description = "Environment name (dev/staging/prod)."
}

# Shared prefix applied to resource names so multiple applications can co-exist in an
# account without collisions. Adjust carefully because it alters many resource identifiers.
variable "name_prefix" {
  type        = string
  description = "Name prefix for resources."
}

# Optional key/value tags that propagate to most resources; use tags for ownership or cost
# allocation metadata, but ensure keys exist in AWS tagging policies before adding them.
variable "tags" {
  type        = map(string)
  description = "Additional tags applied to resources."
  default     = {}
}

# Network
# Defines the IPv4 space available inside the VPC. Pick an address range that will not
# overlap with other networks you plan to peer or connect via VPN.
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
  default     = "10.20.0.0/16"
}

# CIDR blocks for subnets that can host internet-facing resources such as load balancers.
# These ranges must remain within the VPC CIDR and be large enough for EC2 elastic network
# interfaces; /24 is a safe default.
variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets."
  default     = ["10.20.0.0/24", "10.20.1.0/24"]
}

# CIDR blocks for internal subnets that host databases and ECS tasks. Keep them separate
# from public ranges so AWS can apply different routing policies.
variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets."
  default     = ["10.20.10.0/24", "10.20.11.0/24"]
}

# Ordered list of availability zones (e.g. ap-southeast-1a) that the subnets should occupy.
# Spreading across multiple zones increases resiliency but requires matching subnet counts.
variable "availability_zones" {
  type        = list(string)
  description = "Availability zones to use."
}

# Determines whether a NAT gateway is created to give private subnets outbound internet
# access. Disabling it saves money but breaks package downloads and external API calls.
variable "enable_nat_gateway" {
  type        = bool
  description = "Provision a NAT gateway for private subnets."
  default     = true
}

# RDS
# Master username Terraform configures on the Postgres instance. Use a value that meets
# AWS requirements; you will use it for direct administrative access.
variable "rds_master_username" {
  type        = string
  description = "Master username for LiteLLM database."
}

# Master password stored in state (marking as sensitive hides it from CLI output). Rotate
# periodically and never commit real passwords into version control.
variable "rds_master_password" {
  type        = string
  description = "Master password for LiteLLM database."
  sensitive   = true
}

# Name of the initial database schema created on first launch. Application migrations can
# create additional schemas later, but Terraform only manages this initial one.
variable "rds_database_name" {
  type        = string
  description = "Database name for LiteLLM."
  default     = "litellm"
}

# Specific Postgres engine version to run. Upgrades should be planned and tested because
# they may introduce breaking changes or require downtime.
variable "rds_engine_version" {
  type        = string
  description = "PostgreSQL engine version."
  default     = "16.3"
}

# Hardware sizing for the database instance. Smaller sizes cost less but have limited
# CPU/memory. Upsizing usually requires a short outage while AWS re-provisions the host.
variable "rds_instance_class" {
  type        = string
  description = "Instance class for Postgres."
  default     = "db.t4g.micro"
}

# Baseline amount of storage (in GB). Increasing storage can take time; decreasing it is
# impossible without re-creating the database, so choose a safe floor.
variable "rds_allocated_storage" {
  type        = number
  description = "Allocated storage in GB."
  default     = 20
}

# Cap for autoscaling storage. AWS can automatically grow storage up to this amount when
# space runs low, helping avoid outages at the cost of higher spend.
variable "rds_max_allocated_storage" {
  type        = number
  description = "Max autoscaled storage in GB."
  default     = 200
}

# Backing disk performance tier. gp3 fits most workloads; io1/io2 offer provisioned IOPS
# but are more expensive.
variable "rds_storage_type" {
  type        = string
  description = "Storage type for Postgres."
  default     = "gp3"
}

# Enables encryption at rest for database storage. Should remain true in almost all cases
# to meet security best practices.
variable "rds_storage_encrypted" {
  type        = bool
  description = "Enable storage encryption."
  default     = true
}

# Optional customer-managed KMS key ARN. Leave null to let AWS use its managed key if you
# do not need direct control over encryption material.
variable "rds_kms_key_id" {
  type        = string
  description = "KMS key for encryption (optional)."
  default     = null
}

# Toggles Multi-AZ deployments. When true AWS maintains a standby replica in another AZ,
# providing automated failover but doubling cost.
variable "rds_multi_az" {
  type        = bool
  description = "Enable Multi-AZ."
  default     = false
}

# Number of days AWS keeps automated snapshots. Longer retention improves recovery point
# objectives but incurs additional S3 storage charges.
variable "rds_backup_retention_period" {
  type        = number
  description = "Backup retention period."
  default     = 7
}

# When true, Terraform will delete the database immediately without saving a final
# snapshot. Only enable in disposable environments where data loss is acceptable.
variable "rds_skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot on destroy."
  default     = false
}

# Controls whether modifications are rolled out during the next maintenance window (safe)
# or applied right away (quicker but potentially disruptive).
variable "rds_apply_immediately" {
  type        = bool
  description = "Apply RDS changes immediately."
  default     = false
}

# Prevents accidental deletion of the database. Disable only when you intentionally plan
# to destroy the instance.
variable "rds_deletion_protection" {
  type        = bool
  description = "Enable deletion protection."
  default     = true
}

# Enables AWS Performance Insights, a paid feature that captures detailed performance
# metrics useful for troubleshooting slow queries.
variable "rds_performance_insights_enabled" {
  type        = bool
  description = "Enable Performance Insights."
  default     = false
}

# Optional KMS key for encrypting Performance Insights data. Required if your account
# enforces the use of customer-managed keys.
variable "rds_performance_insights_kms_key_id" {
  type        = string
  description = "KMS key for Performance Insights."
  default     = null
}

# Extra security groups that should be allowed to connect to Postgres (for example, BI
# tooling or bastion hosts). Ensure each group enforces its own ingress rules.
variable "additional_rds_allowed_security_group_ids" {
  type        = list(string)
  description = "Extra security groups allowed to access Postgres."
  default     = []
}

# Redis
# Specific Redis engine version. Newer versions bring features and fixes but require
# compatibility testing with your application client libraries.
variable "redis_engine_version" {
  type        = string
  description = "Redis engine version."
  default     = "7.1"
}

# Determines CPU and memory for each Redis node. Larger node types support more concurrent
# connections and larger datasets but cost more per hour.
variable "redis_node_type" {
  type        = string
  description = "Instance type for Redis."
  default     = "cache.t4g.small"
}

# Number of cache nodes when cluster mode is disabled. A single node is simplest but lacks
# high availability.
variable "redis_num_cache_nodes" {
  type        = number
  description = "Number of cache nodes when cluster mode disabled."
  default     = 1
}

# Switches between classic (single primary/replica) and cluster (sharded) architectures.
# Cluster mode is required for datasets larger than a single node can support.
variable "redis_cluster_mode_enabled" {
  type        = bool
  description = "Enable Redis cluster mode."
  default     = false
}

# Number of shards to create when cluster mode is enabled. More shards distribute load but
# add operational complexity.
variable "redis_num_node_groups" {
  type        = number
  description = "Number of shards when cluster mode enabled."
  default     = null
}

# Number of replicas per shard in cluster mode. Replicas provide read scaling and failover
# but each replica incurs additional cost.
variable "redis_replicas_per_node_group" {
  type        = number
  description = "Replicas per node group when cluster mode enabled."
  default     = null
}

# Enables automatic promotion of replicas if the primary fails. Requires at least one
# replica per node group and improves availability.
variable "redis_automatic_failover_enabled" {
  type        = bool
  description = "Enable Redis automatic failover."
  default     = false
}

# Ensures primary and replica nodes live in different availability zones. Recommended for
# production resiliency but slightly increases latency.
variable "redis_multi_az_enabled" {
  type        = bool
  description = "Enable Redis Multi-AZ."
  default     = false
}

# Encrypts traffic between clients and Redis. Keep enabled unless every client runs within
# a fully trusted network.
variable "redis_transit_encryption_enabled" {
  type        = bool
  description = "Enable in-transit encryption."
  default     = true
}

# Encrypts the cache data stored on disk. Recommended to satisfy security compliance.
variable "redis_at_rest_encryption_enabled" {
  type        = bool
  description = "Enable at-rest encryption."
  default     = true
}

# Optional password clients must present. Provide an SSM Parameter Store or Secrets Manager
# ARN so the token is not stored in plain text.
variable "redis_auth_token" {
  type        = string
  description = "Redis AUTH token (Secrets Manager or SSM ARN)."
  default     = null
  sensitive   = true
}

# UTC time window when AWS may apply patches. Pick off-peak hours to minimise disruption
# if you choose to set a specific window.
variable "redis_maintenance_window" {
  type        = string
  description = "Preferred maintenance window."
  default     = null
}

# Preferred timeframe for daily snapshots. Schedule away from peak load to reduce the
# chance of performance impact.
variable "redis_snapshot_window" {
  type        = string
  description = "Preferred snapshot window."
  default     = null
}

# Number of days to retain Redis snapshots. Zero disables snapshots; increase for disaster
# recovery at the cost of additional storage.
variable "redis_snapshot_retention_limit" {
  type        = number
  description = "Snapshot retention days."
  default     = 0
}

# Controls which availability zones host the cache nodes when you need deterministic
# placement. Leave empty to let AWS balance automatically.
variable "redis_preferred_cache_cluster_azs" {
  type        = list(string)
  description = "Preferred AZs for cache clusters."
  default     = []
}

# TCP port clients use to reach Redis. Only change if organisational policies require a
# non-default port and update security groups accordingly.
variable "redis_port" {
  type        = number
  description = "Redis port."
  default     = 6379
}

# Additional security groups that should be able to reach Redis beyond the default ECS
# service group—useful for admin tooling or batch jobs.
variable "additional_redis_allowed_security_group_ids" {
  type        = list(string)
  description = "Extra security groups allowed to access Redis."
  default     = []
}

# LiteLLM ECS
# Full ECR (or Docker Hub) image URI that Fargate pulls when starting the task. Update
# this when shipping new application versions.
variable "litellm_container_image" {
  type        = string
  description = "Full image URI for LiteLLM container."
}

# Overrides the default container entrypoint. Useful for injecting CLI flags without
# rebuilding the image.
variable "litellm_container_command" {
  type        = list(string)
  description = "Override command for LiteLLM container."
  default     = ["--config", "/app/config.yaml", "--port", "4000", "--num_workers", "2"]
}

# Internal port the container listens on. Must match the service's security group rules and
# load balancer target group configuration.
variable "litellm_container_port" {
  type        = number
  description = "Port exposed by LiteLLM container."
  default     = 4000
}

# Number of task replicas ECS should keep running. Higher counts provide redundancy and
# throughput at the cost of additional compute spend.
variable "litellm_desired_count" {
  type        = number
  description = "Desired ECS task count."
  default     = 1
}

# CPU units allocated per task. Fargate enforces mappings between CPU and memory; refer to
# AWS docs before changing to ensure the pair remains valid.
variable "litellm_task_cpu" {
  type        = string
  description = "Task CPU units."
  default     = "1024"
}

# Memory (MiB) allocated per task. Setting this too low leads to OutOfMemory restarts,
# while larger values increase cost.
variable "litellm_task_memory" {
  type        = string
  description = "Task memory (MiB)."
  default     = "2048"
}

# Determines whether Fargate attaches public IPs to task ENIs. Required only when tasks in
# private subnets need direct internet access and no NAT gateway exists.
variable "litellm_assign_public_ip" {
  type        = bool
  description = "Assign public IPs to LiteLLM tasks."
  default     = false
}

# Plain-text environment variables injected into the container. Good place for non-secret
# feature flags or configuration.
variable "litellm_environment" {
  type        = map(string)
  description = "Additional non-secret environment variables for LiteLLM."
  default     = {}
}

# Map of environment variable names to SSM/Secrets Manager ARNs. The ECS module converts
# this into secure environment variables so secrets never live in plain text.
variable "litellm_secrets" {
  type        = map(string)
  description = "Map of LiteLLM environment variable names to secret ARNs (SSM or Secrets Manager)."
  default     = {}
}

# File path inside the container where LiteLLM should load its config. Changing this must
# align with the container image layout.
variable "litellm_config_path" {
  type        = string
  description = "Path to the LiteLLM config inside the container."
  default     = "/app/config.yaml"
}

# HTTP endpoint the load balancer calls to verify task health. Ensure the application
# responds quickly with a 2xx/3xx status.
variable "litellm_health_check_path" {
  type        = string
  description = "HTTP path used by ALB health checks."
  default     = "/health/readiness"
}

# Number of days CloudWatch retains logs. Increase for audit needs, decrease to control
# storage cost.
variable "litellm_log_retention_days" {
  type        = number
  description = "CloudWatch Logs retention."
  default     = 14
}

# Extra security groups attached to the ECS service ENIs. Use this to grant access to
# shared services without modifying the core module.
variable "additional_service_security_group_ids" {
  type        = list(string)
  description = "Extra security groups to attach to LiteLLM service ENIs."
  default     = []
}

# ALB
# List of IPv4 CIDR ranges allowed through the Application Load Balancer security group.
# Leaving it open to 0.0.0.0/0 exposes the service to the internet; tighten for private apps.
variable "alb_ingress_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed to reach the ALB."
  default     = ["0.0.0.0/0"]
}

# TCP port exposed on the ALB listener. 80 handles HTTP; use 443 with an ACM certificate to
# terminate TLS if required.
variable "alb_listener_port" {
  type        = number
  description = "Port for the ALB HTTP listener."
  default     = 80
}

# Protects the ALB from accidental deletion. Enable in production to avoid unplanned
# downtime.
variable "alb_deletion_protection" {
  type        = bool
  description = "Enable ALB deletion protection."
  default     = false
}
