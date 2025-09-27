# Provide downstream modules with the identifiers they need to attach resources to this
# network without recomputing them.
output "vpc_id" {
  description = "ID of the provisioned VPC for peering or security-group associations."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "List of subnet IDs that expose resources to the internet (e.g. ALBs)."
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "List of private subnet IDs suitable for databases or ECS services."
  value       = [for s in aws_subnet.private : s.id]
}

output "private_route_table_id" {
  description = "Route table handling private subnet egress, null when no private subnets exist."
  value       = length(aws_route_table.private) > 0 ? aws_route_table.private[0].id : null
}
