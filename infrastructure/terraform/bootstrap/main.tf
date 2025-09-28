// Bootstrap stack that builds the remote state storage (S3 bucket + DynamoDB lock table)
// required before any other Terraform configurations can run safely.

terraform {
  # Require Terraform 1.6 or newer so that the backend configuration syntax and provider
  # behavior align with this configuration.
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      # Pull the official AWS provider from the HashiCorp registry.
      source = "hashicorp/aws"
      # Allow all 5.x versions to receive bug fixes without risking breaking changes from 6.x.
      version = "~> 5.0"
    }
  }
}

# Global AWS provider definition; every resource below inherits this region setting.
provider "aws" {
  region = var.aws_region
}

# Shared tagging structure so the bucket and table carry consistent metadata.
locals {
  tags = merge(var.tags, {
    Application = "terraform-backend"
    Component   = "bootstrap"
  })
}

# S3 bucket that stores Terraform state files. Must exist before enabling remote state.
resource "aws_s3_bucket" "state" {
  bucket = var.state_bucket_name

  tags = merge(local.tags, {
    Name = var.state_bucket_name
  })
}

# Enable bucket versioning so we can recover previous state files if a deployment corrupts
# the latest version.
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enforce server-side encryption on every object written to the state bucket.
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all forms of public access to the bucket, ensuring sensitive state data stays private.
resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# DynamoDB table that Terraform uses to acquire a state lock, preventing concurrent writes.
resource "aws_dynamodb_table" "lock" {
  name = var.lock_table_name
  # On-demand billing keeps cost low and avoids capacity management.
  billing_mode = "PAY_PER_REQUEST"
  # Terraform locks on a single partition key containing the state file path.
  hash_key = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Point-in-time recovery lets us restore accidentally deleted lock records.
  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.tags, {
    Name = var.lock_table_name
  })
}

# Surface identifiers for reuse in other scripts or documentation.
output "state_bucket_name" {
  description = "Name of the S3 bucket storing Terraform state, for configuring backends."
  value       = aws_s3_bucket.state.id
}

output "lock_table_name" {
  description = "Name of the DynamoDB table Terraform uses for state locking."
  value       = aws_dynamodb_table.lock.name
}
