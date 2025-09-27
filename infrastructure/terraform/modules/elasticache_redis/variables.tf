# Unique identifier for the Redis replication group. Appears in AWS consoles and logs.
variable "name" {
  type        = string
  description = "Replication group identifier."
}

# Free-form description that shows up in the AWS console; explain the cluster's purpose.
variable "description" {
  type        = string
  description = "Description for the replication group."
  default     = "Managed by Terraform"
}

# VPC where the cache runs so security groups and subnets line up with the rest of the stack.
variable "vpc_id" {
  type        = string
  description = "VPC ID for the cache."
}

# Subnets that host the cache nodes. Provide private subnet IDs to keep Redis internal.
variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for the cache subnet group."
}

# Security groups granted inbound access to Redis, typically application services.
variable "allowed_security_group_ids" {
  type        = list(string)
  description = "Security groups allowed to reach Redis."
  default     = []
}

# Additional security groups attached directly to the Redis ENIs. Useful for monitoring or
# management tooling that must initiate connections from the cache to other services.
variable "extra_security_group_ids" {
  type        = list(string)
  description = "Additional security groups to attach."
  default     = []
}

# Redis software version to run. Align with application compatibility testing before upgrades.
variable "engine_version" {
  type        = string
  description = "Redis engine version."
  default     = "7.1"
}

# Optional custom parameter group for fine-tuning Redis settings beyond the defaults.
variable "parameter_group_name" {
  type        = string
  description = "Custom parameter group name."
  default     = null
}

# Hardware class for each cache node. Larger types handle more connections and data but cost more.
variable "node_type" {
  type        = string
  description = "Instance type for the cache nodes."
  default     = "cache.t4g.small"
}

# Number of cache nodes when running in classic (non-cluster) mode. Typically 1 primary + replicas.
variable "num_cache_nodes" {
  type        = number
  description = "Number of cache nodes (when cluster mode disabled)."
  default     = 1
}

# Enables partitioned Redis (cluster mode). Required for datasets that exceed single-node memory limits.
variable "cluster_mode_enabled" {
  type        = bool
  description = "Enable cluster mode."
  default     = false
}

# Number of shards in cluster mode. More shards distribute data and requests across nodes.
variable "num_node_groups" {
  type        = number
  description = "Number of node groups (shards) when cluster mode enabled."
  default     = null
}

# How many replica nodes each shard maintains. Replicas add redundancy and can serve reads.
variable "replicas_per_node_group" {
  type        = number
  description = "Replicas per node group when cluster mode enabled."
  default     = null
}

# Automatically promote replicas when a primary fails. Requires replicas to be configured.
variable "automatic_failover_enabled" {
  type        = bool
  description = "Enable automatic failover."
  default     = true
}

# Spreads nodes across multiple availability zones to improve resilience to AZ outages.
variable "multi_az_enabled" {
  type        = bool
  description = "Enable Multi-AZ."
  default     = true
}

# Encrypts traffic between clients and Redis to guard against packet sniffing.
variable "transit_encryption_enabled" {
  type        = bool
  description = "Enable in-transit encryption."
  default     = true
}

# Encrypts data stored on disk (snapshots, swap). Keep enabled to satisfy security policies.
variable "at_rest_encryption_enabled" {
  type        = bool
  description = "Enable at-rest encryption."
  default     = true
}

# Optional Redis AUTH token. Provide via SSM/Secrets Manager to avoid storing secrets in code.
variable "auth_token" {
  type        = string
  description = "AUTH token for Redis."
  default     = null
  sensitive   = true
}

# Weekly maintenance window in ddd:hh24:mi format. Choose a quiet period to minimise impact.
variable "maintenance_window" {
  type        = string
  description = "Preferred maintenance window."
  default     = null
}

# Daily snapshot window (UTC). Schedule when load is low to avoid latency spikes.
variable "snapshot_window" {
  type        = string
  description = "Preferred snapshot window."
  default     = null
}

# Number of daily snapshots to retain. Higher values improve recovery options at additional cost.
variable "snapshot_retention_limit" {
  type        = number
  description = "Number of days to retain snapshots."
  default     = 0
}

# Optional list of preferred availability zones for the cache nodes. Leave empty for automatic placement.
variable "preferred_cache_cluster_azs" {
  type        = list(string)
  description = "Preferred AZs for cache clusters."
  default     = []
}

# TCP port clients use to connect. Default 6379 works for most deployments.
variable "port" {
  type        = number
  description = "Port Redis listens on."
  default     = 6379
}

# Arbitrary tags propagated to every resource the module creates.
variable "tags" {
  type        = map(string)
  description = "Resource tags."
  default     = {}
}
