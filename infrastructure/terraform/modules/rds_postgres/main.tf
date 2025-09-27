// Module that provisions a single RDS PostgreSQL instance with secure networking defaults.

# Subnet group confines the database to the specified private subnets.
resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids
  tags = merge(var.tags, {
    Name = "${var.name}-subnet-group"
  })
}

# Security group controls inbound access to the database. Outbound is left open for AWS APIs.
resource "aws_security_group" "this" {
  name        = "${var.name}-sg"
  description = "Security group for ${var.name} RDS"
  vpc_id      = var.vpc_id
  tags = merge(var.tags, {
    Name = "${var.name}-sg"
  })
}

# Permit application security groups to open TCP connections to Postgres.
resource "aws_security_group_rule" "ingress" {
  count = length(var.allowed_security_group_ids)

  security_group_id        = aws_security_group.this.id
  type                     = "ingress"
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = var.allowed_security_group_ids[count.index]
}

# Allow outbound traffic so the instance can reach AWS services like CloudWatch Logs.
resource "aws_security_group_rule" "egress" {
  security_group_id = aws_security_group.this.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
}

# Managed PostgreSQL instance with encryption, backups, and optional multi-AZ support.
resource "aws_db_instance" "this" {
  identifier                      = var.name
  engine                          = "postgres"
  engine_version                  = var.engine_version
  instance_class                  = var.instance_class
  username                        = var.username
  password                        = var.password
  db_name                         = var.db_name
  allocated_storage               = var.allocated_storage
  max_allocated_storage           = var.max_allocated_storage
  storage_type                    = var.storage_type
  storage_encrypted               = var.storage_encrypted
  kms_key_id                      = var.kms_key_id
  multi_az                        = var.multi_az
  db_subnet_group_name            = aws_db_subnet_group.this.name
  vpc_security_group_ids          = concat([aws_security_group.this.id], var.extra_security_group_ids)
  backup_retention_period         = var.backup_retention_period
  skip_final_snapshot             = var.skip_final_snapshot
  apply_immediately               = var.apply_immediately
  deletion_protection             = var.deletion_protection
  publicly_accessible             = false
  port                            = var.port
  performance_insights_enabled    = var.performance_insights_enabled
  performance_insights_kms_key_id = var.performance_insights_kms_key_id
  tags = merge(var.tags, {
    Name = var.name
  })
}
