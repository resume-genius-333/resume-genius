# Unique identifier for the database instance and its related resources.
variable "name" {
  type        = string
  description = "Identifier for the RDS instance."
}

# VPC where the database resides so networking aligns with application workloads.
variable "vpc_id" {
  type        = string
  description = "VPC ID where the instance will reside."
}

# Private subnet IDs that form the DB subnet group. Choose subnets across multiple AZs for HA.
variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for the DB subnet group."
}

# Security groups permitted to initiate connections to the database.
variable "allowed_security_group_ids" {
  type        = list(string)
  description = "Security group IDs allowed to reach the database."
  default     = []
}

# Additional security groups attached directly to the DB instance for outbound rules or monitoring.
variable "extra_security_group_ids" {
  type        = list(string)
  description = "Additional security groups to attach to the DB instance."
  default     = []
}

# Specific PostgreSQL engine version to run. Plan upgrades carefully to avoid incompatible changes.
variable "engine_version" {
  type        = string
  description = "PostgreSQL engine version."
  default     = "16.3"
}

# Compute/memory footprint of the instance. Smaller classes cost less but may bottleneck under load.
variable "instance_class" {
  type        = string
  description = "Instance class for the database."
  default     = "db.t4g.micro"
}

# Administrative username created during provisioning.
variable "username" {
  type        = string
  description = "Master username for the database."
}

# Administrative password. Marked sensitive to keep it out of plan output; still avoid committing real values.
variable "password" {
  type        = string
  description = "Master password for the database."
  sensitive   = true
}

# Initial database created within the instance for LiteLLM to use.
variable "db_name" {
  type        = string
  description = "Initial database name to create."
}

# Starting storage allocation in GB. Can be increased later but not reduced without rebuilding.
variable "allocated_storage" {
  type        = number
  description = "Initial storage (GB)."
  default     = 20
}

# Upper bound for autoscaling storage. AWS grows storage as needed up to this limit to prevent outages.
variable "max_allocated_storage" {
  type        = number
  description = "Maximum storage (GB) for autoscaling."
  default     = 100
}

# Storage type determines IO characteristics. gp3 suits general workloads; io1/io2 provide provisioned IOPS.
variable "storage_type" {
  type        = string
  description = "Storage type (gp2, gp3, io1)."
  default     = "gp3"
}

# Enables encryption at rest. Should remain true for production deployments.
variable "storage_encrypted" {
  type        = bool
  description = "Enable storage encryption."
  default     = true
}

# Optional customer-managed KMS key for encryption. Leave null for AWS-managed default.
variable "kms_key_id" {
  type        = string
  description = "KMS key ARN for encryption (optional)."
  default     = null
}

# Adds a synchronous standby in another AZ for automatic failover at higher cost.
variable "multi_az" {
  type        = bool
  description = "Enable Multi-AZ deployment."
  default     = false
}

# Number of days AWS keeps automated backups.
variable "backup_retention_period" {
  type        = number
  description = "Days to retain backups."
  default     = 7
}

# Skip creating a snapshot before deletion. Only set true for disposable environments.
variable "skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot on destroy. Use only for non-prod."
  default     = false
}

# Controls whether updates happen instantly (risking downtime) or during maintenance windows.
variable "apply_immediately" {
  type        = bool
  description = "Apply modifications immediately."
  default     = false
}

# Prevents accidental deletion of the database instance.
variable "deletion_protection" {
  type        = bool
  description = "Enable deletion protection."
  default     = true
}

# TCP port for Postgres traffic. Default 5432 is standard.
variable "port" {
  type        = number
  description = "Database port."
  default     = 5432
}

# Enables Performance Insights for deep query analysis; incurs additional charges.
variable "performance_insights_enabled" {
  type        = bool
  description = "Enable Performance Insights."
  default     = false
}

# Optional KMS key for encrypting Performance Insights metrics.
variable "performance_insights_kms_key_id" {
  type        = string
  description = "KMS key for Performance Insights."
  default     = null
}

# Arbitrary tags applied to each resource the module provisions.
variable "tags" {
  type        = map(string)
  description = "Resource tags."
  default     = {}
}
