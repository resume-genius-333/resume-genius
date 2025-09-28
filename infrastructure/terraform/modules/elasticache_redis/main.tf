// Standalone module that provisions an ElastiCache Redis replication group along with the
// supporting networking controls (subnet group + security groups).

# Subnet group limits the cache nodes to the specified private subnets.
resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids
  tags = merge(var.tags, {
    Name = "${var.name}-subnet-group"
  })
}

# Security group that controls inbound access to Redis. Outbound traffic is unrestricted so
# the service can reach AWS APIs when necessary.
resource "aws_security_group" "this" {
  name        = "${var.name}-sg"
  description = "Security group for ${var.name} redis"
  vpc_id      = var.vpc_id
  tags = merge(var.tags, {
    Name = "${var.name}-sg"
  })
}

# Allow inbound connections from approved security groups on the Redis TCP port. Using
# security groups instead of CIDR blocks keeps connectivity scoped to trusted services.
resource "aws_security_group_rule" "ingress" {
  count = length(var.allowed_security_group_ids)

  security_group_id        = aws_security_group.this.id
  type                     = "ingress"
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = var.allowed_security_group_ids[count.index]
}

# Allow outbound traffic so the cache can contact other AWS services (e.g. monitoring APIs).
resource "aws_security_group_rule" "egress" {
  security_group_id = aws_security_group.this.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
}

# Core Redis replication group configuration. Handles both classic and cluster-mode setups.
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = var.description
  engine               = "redis"
  engine_version       = var.engine_version
  parameter_group_name = var.parameter_group_name
  node_type            = var.node_type
  # Classic mode uses num_cache_nodes, cluster mode uses node groups + replicas.
  replicas_per_node_group     = var.cluster_mode_enabled ? var.replicas_per_node_group : null
  num_node_groups             = var.cluster_mode_enabled ? var.num_node_groups : null
  automatic_failover_enabled  = var.automatic_failover_enabled
  multi_az_enabled            = var.multi_az_enabled
  transit_encryption_enabled  = var.transit_encryption_enabled
  at_rest_encryption_enabled  = var.at_rest_encryption_enabled
  auth_token                  = var.auth_token
  security_group_ids          = concat([aws_security_group.this.id], var.extra_security_group_ids)
  subnet_group_name           = aws_elasticache_subnet_group.this.name
  preferred_cache_cluster_azs = var.preferred_cache_cluster_azs
  maintenance_window          = var.maintenance_window
  snapshot_window             = var.snapshot_window
  snapshot_retention_limit    = var.snapshot_retention_limit
  auto_minor_version_upgrade  = true
  tags = merge(var.tags, {
    Name = var.name
  })

  lifecycle {
    # Allow operators to rotate the auth token out-of-band without Terraform forcing a
    # replacement of the cache cluster.
    ignore_changes = [auth_token]
  }
}
