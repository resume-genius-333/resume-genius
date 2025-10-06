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
  value       = var.backend_rds_enabled ? module.backend_rds[0].endpoint : null
}

output "backend_rds_hostname" {
  description = "Preferred hostname (custom alias when configured) for the backend database."
  value       = local.backend_rds_hostname
}

output "litellm_manual_control_api_url" {
  description = "Invoke URL for the LiteLLM manual override API."
  value       = var.litellm_manual_control_enabled ? aws_apigatewayv2_stage.litellm_control[0].invoke_url : null
}

output "backend_db_bastion_instance_id" {
  description = "Instance ID of the SSM-managed bastion host used for database access."
  value       = var.backend_db_bastion_enabled ? aws_instance.backend_db_bastion[0].id : null
}

output "backend_db_bastion_public_dns" {
  description = "Public DNS name of the bastion (useful for debugging)."
  value       = var.backend_db_bastion_enabled ? aws_instance.backend_db_bastion[0].public_dns : null
}

output "backend_rds_secret_arn" {
  description = "ARN of the Secrets Manager secret that stores backend DB credentials."
  value       = try(aws_secretsmanager_secret.backend_db[0].arn, null)
}

output "backend_security_group_id" {
  description = "Security group ID assigned to backend services for database access."
  value       = aws_security_group.backend_internal.id
}

output "resume_genius_backend_rds_connection" {
  description = "Connection details for the public Resume Genius development database."
  value = {
    host       = aws_db_instance.resume_genius_backend.address
    port       = aws_db_instance.resume_genius_backend.port
    database   = var.resume_genius_backend_rds_database_name
    username   = var.resume_genius_backend_rds_master_username
    secret_arn = aws_secretsmanager_secret.resume_genius_backend.arn
  }
}
