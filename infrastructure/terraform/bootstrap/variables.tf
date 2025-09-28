# Region where the bootstrap resources will live. All subsequent Terraform configurations
# must point their backend to the same region so they can find the bucket and table.
variable "aws_region" {
  type        = string
  description = "AWS region to deploy bootstrap resources."
}

# Globally unique name for the S3 bucket that stores Terraform state files. Bucket names
# cannot be reused once taken, so choose carefully.
variable "state_bucket_name" {
  type        = string
  description = "Globally-unique name for the Terraform state bucket."
}

# DynamoDB table that Terraform uses to coordinate state locking. Use a descriptive name so
# operators can identify its purpose in the AWS console.
variable "lock_table_name" {
  type        = string
  description = "Name of the DynamoDB table for Terraform state locking."
}

# Optional shared tag map applied to the bucket and table. Helpful for designating owners or
# cost centres; keep values consistent across environments.
variable "tags" {
  type        = map(string)
  description = "Additional tags applied to bootstrap resources."
  default     = {}
}
