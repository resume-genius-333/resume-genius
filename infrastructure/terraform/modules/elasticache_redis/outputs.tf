# Surface connection details and identifiers so callers can configure clients and IAM.
output "primary_endpoint_address" {
  description = "Primary endpoint for Redis connections (read/write traffic)."
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Load-balanced reader endpoint, available only when replicas exist."
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "TCP port Redis listens on so security groups can align."
  value       = var.port
}

output "security_group_id" {
  description = "Security group guarding Redis; attach it to clients that require access."
  value       = aws_security_group.this.id
}

output "arn" {
  description = "Full ARN of the replication group for IAM policies or monitoring."
  value       = aws_elasticache_replication_group.this.arn
}
