// Minimal, publicly accessible Postgres instance for the Resume Genius backend so local
// development can connect without docker-compose. This intentionally trades security for
// convenience; restrict the allowed CIDRs in production environments.

locals {
  resume_genius_backend_rds_identifier = var.resume_genius_backend_rds_identifier
  resume_genius_backend_rds_port       = 5432
  resume_genius_backend_rds_secret_name = coalesce(
    var.resume_genius_backend_rds_secret_name,
    "${var.name_prefix}-${var.environment}-resume-genius-backend"
  )
}

resource "random_password" "resume_genius_backend" {
  length           = var.resume_genius_backend_rds_master_password_length
  special          = true
  override_special = "!#$%&*-_=+"
  min_lower        = 1
  min_upper        = 1
  min_numeric      = 1
  min_special      = 1

  keepers = {
    identifier = local.resume_genius_backend_rds_identifier
  }
}

resource "aws_secretsmanager_secret" "resume_genius_backend" {
  name        = local.resume_genius_backend_rds_secret_name
  description = "Credentials for the ${local.resume_genius_backend_rds_identifier} development Postgres instance"

  tags = merge(local.tags, {
    Name = local.resume_genius_backend_rds_secret_name
  })
}

resource "aws_secretsmanager_secret_version" "resume_genius_backend" {
  secret_id = aws_secretsmanager_secret.resume_genius_backend.id
  secret_string = jsonencode({
    master_username = var.resume_genius_backend_rds_master_username
    master_password = random_password.resume_genius_backend.result
    database_name   = var.resume_genius_backend_rds_database_name
  })
}

resource "aws_db_subnet_group" "resume_genius_backend" {
  name       = "${local.resume_genius_backend_rds_identifier}-subnet-group"
  subnet_ids = module.network.public_subnet_ids

  tags = merge(local.tags, {
    Name = "${local.resume_genius_backend_rds_identifier}-subnet-group"
  })
}

resource "aws_security_group" "resume_genius_backend" {
  name        = "${local.resume_genius_backend_rds_identifier}-public"
  description = "Public access for ${local.resume_genius_backend_rds_identifier} Postgres"
  vpc_id      = module.network.vpc_id

  tags = merge(local.tags, {
    Name = "${local.resume_genius_backend_rds_identifier}-public"
  })
}

resource "aws_security_group_rule" "resume_genius_backend_ingress" {
  count = length(var.resume_genius_backend_rds_allowed_cidrs)

  security_group_id = aws_security_group.resume_genius_backend.id
  type              = "ingress"
  from_port         = local.resume_genius_backend_rds_port
  to_port           = local.resume_genius_backend_rds_port
  protocol          = "tcp"
  cidr_blocks       = [var.resume_genius_backend_rds_allowed_cidrs[count.index]]
}

resource "aws_security_group_rule" "resume_genius_backend_egress" {
  security_group_id = aws_security_group.resume_genius_backend.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
}

resource "aws_db_instance" "resume_genius_backend" {
  identifier                 = local.resume_genius_backend_rds_identifier
  engine                     = "postgres"
  engine_version             = var.rds_engine_version
  instance_class             = var.rds_instance_class
  allocated_storage          = var.rds_allocated_storage
  max_allocated_storage      = var.rds_max_allocated_storage
  username                   = var.resume_genius_backend_rds_master_username
  password                   = random_password.resume_genius_backend.result
  db_name                    = var.resume_genius_backend_rds_database_name
  db_subnet_group_name       = aws_db_subnet_group.resume_genius_backend.name
  vpc_security_group_ids     = [aws_security_group.resume_genius_backend.id]
  publicly_accessible        = true
  port                       = local.resume_genius_backend_rds_port
  backup_retention_period    = 0
  skip_final_snapshot        = true
  apply_immediately          = true
  deletion_protection        = false
  auto_minor_version_upgrade = true

  tags = merge(local.tags, {
    Name = local.resume_genius_backend_rds_identifier
  })
}
