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

output "redis_endpoint" {
  description = "Hostname clients use to connect to the primary Redis node for read/write traffic."
  value       = module.redis.primary_endpoint_address
}
