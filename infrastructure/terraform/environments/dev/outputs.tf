# Expose frequently referenced identifiers so operators and other modules can easily link
# to the resources Terraform creates.
output "vpc_id" {
  description = "ID of the VPC so other stacks can attach subnets or security groups to it."
  value       = module.network.vpc_id
}

output "litellm_alb_dns_name" {
  description = "Public DNS hostname clients use to reach LiteLLM through the load balancer."
  value       = module.litellm.alb_dns_name
}

output "litellm_service_name" {
  description = "ECS service identifier, useful for debugging deployments or creating alarms."
  value       = module.litellm.service_name
}

output "litellm_cluster_name" {
  description = "Name of the ECS cluster hosting LiteLLM tasks, referenced by scaling policies."
  value       = module.litellm.cluster_name
}

output "rds_endpoint" {
  description = "Network address applications use when connecting to the Postgres database."
  value       = module.rds.endpoint
}

output "litellm_cache_bucket" {
  description = "Name of the S3 bucket storing LiteLLM cached responses."
  value       = aws_s3_bucket.litellm_cache.bucket
}

output "backend_rds_endpoint" {
  description = "Hostname for the Resume Genius backend database."
  value       = module.backend_rds.endpoint
}

output "backend_rds_hostname" {
  description = "Preferred hostname (custom alias when configured) for the backend database."
  value       = local.backend_rds_hostname
}

output "backend_rds_secret_arn" {
  description = "ARN of the Secrets Manager secret that stores backend DB credentials."
  value       = aws_secretsmanager_secret.backend_db.arn
}

output "backend_security_group_id" {
  description = "Security group ID assigned to backend services for database access."
  value       = aws_security_group.backend_internal.id
}
