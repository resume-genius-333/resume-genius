# Expose connection points and IAM references that callers frequently need.
output "cluster_name" {
  description = "Name of the ECS cluster for debugging or CloudWatch alarms."
  value       = aws_ecs_cluster.this.name
}

output "service_name" {
  description = "Name of the ECS service so operators can issue scale commands."
  value       = aws_ecs_service.this.name
}

output "task_role_arn" {
  description = "ARN of the IAM role assumed by LiteLLM tasks (grant app permissions here)."
  value       = aws_iam_role.task.arn
}

output "service_security_group_id" {
  description = "Security group attached to service ENIs, useful for whitelisting access."
  value       = aws_security_group.service.id
}

output "alb_dns_name" {
  description = "Public DNS name clients use to reach the service through the ALB."
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer for IAM and tagging references."
  value       = aws_lb.this.arn
}

output "target_group_arn" {
  description = "ARN of the target group registered with the ECS service."
  value       = aws_lb_target_group.this.arn
}
