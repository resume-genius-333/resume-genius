# Provide connection and identification details other modules or operators may need.
output "endpoint" {
  description = "Hostname applications use to reach the primary Postgres instance."
  value       = aws_db_instance.this.endpoint
}

output "port" {
  description = "TCP port that Postgres listens on (useful for security groups)."
  value       = aws_db_instance.this.port
}

output "security_group_id" {
  description = "Security group controlling database ingress; share with trusted clients."
  value       = aws_security_group.this.id
}

output "arn" {
  description = "Full ARN of the DB instance for IAM policies or monitoring."
  value       = aws_db_instance.this.arn
}

output "identifier" {
  description = "Resource identifier that appears in AWS consoles and CLI responses."
  value       = aws_db_instance.this.id
}
