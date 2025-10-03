
# Prefix applied to all ECS/ALB resources. Helps identify which environment they belong to.
variable "name_prefix" {
  type        = string
  description = "Prefix for ECS resources."
}

# AWS region value used both by resources and the log driver configuration.
variable "aws_region" {
  type        = string
  description = "AWS region (used for logging configuration)."
}

# Container image reference (e.g. ECR URI). Update this when releasing new LiteLLM versions.
variable "container_image" {
  type        = string
  description = "Container image URI for LiteLLM."
}

# Internal port the application listens on. Must align with service security groups and ALB target group.
variable "container_port" {
  type        = number
  description = "Container port to expose."
  default     = 4000
}

# Optional override for the command executed when the container starts.
variable "container_command" {
  type        = list(string)
  description = "Override container command."
  default     = []
}

# Plain-text environment variables passed into the container at runtime.
variable "environment" {
  type        = map(string)
  description = "Plain environment variables for the container."
  default     = {}
}

# Structured list of secrets to inject as environment variables without exposing plaintext in state.
variable "secrets" {
  type = list(object({
    name       = string
    value_from = string
  }))
  description = "Secrets to inject into the container (SSM or Secrets Manager ARNs)."
  default     = []
}

# Flattened list of all secret ARNs referenced above. Used to build IAM policies granting read access.
variable "secret_arns" {
  type        = list(string)
  description = "Unique list of secret ARNs required for IAM permissions."
  default     = []
}

# Private subnets where the ECS tasks run. Choose subnets with outbound access via NAT.
variable "subnet_ids" {
  type        = list(string)
  description = "Private subnets for the ECS service."
}

# Public subnets that host the Application Load Balancer.
variable "alb_subnet_ids" {
  type        = list(string)
  description = "Public subnets for the ALB."
}

# CIDR blocks allowed to reach the ALB. Restrict this list for private deployments.
variable "alb_ingress_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed to reach the ALB."
  default     = ["0.0.0.0/0"]
}

# VPC that contains both the ALB and ECS service.
variable "vpc_id" {
  type        = string
  description = "VPC ID."
}

# Number of parallel task replicas to run. Increase for redundancy and throughput.
variable "desired_count" {
  type        = number
  description = "Desired task count."
  default     = 1
}

# CPU units reserved per task. Must follow Fargate's allowed CPU/memory combinations.
variable "task_cpu" {
  type        = string
  description = "CPU units for the task (e.g. 512)."
  default     = "512"
}

# Memory in MiB allocated per task container.
variable "task_memory" {
  type        = string
  description = "Memory for the task (e.g. 1024)."
  default     = "1024"
}

# When true, tasks receive public IPs directly. Only needed in public subnets or when no NAT exists.
variable "assign_public_ip" {
  type        = bool
  description = "Assign public IP to Fargate tasks."
  default     = false
}

# Enables ECS Exec so operators can open SSM sessions into running tasks. Requires the task
# role to have SSM message permissions and network access to the SSM endpoints.
variable "enable_execute_command" {
  type        = bool
  description = "Enable ECS Exec (SSM) connectivity to the service tasks."
  default     = false
}

# Additional security groups attached to the task ENIs. Use this to grant access to shared services.
variable "additional_service_security_groups" {
  type        = list(string)
  description = "Extra security groups to attach to the service ENIs."
  default     = []
}

# Path the target group polls to ensure tasks are healthy before routing traffic.
variable "health_check_path" {
  type        = string
  description = "HTTP health-check path for the target group."
  default     = "/health"
}

# Port exposed on the ALB listener. Use 443 with TLS termination if you attach an ACM certificate.
variable "listener_port" {
  type        = number
  description = "Listener port for the ALB."
  default     = 80
}

# TCP port used for the HTTPS listener when TLS termination is enabled.
variable "https_listener_port" {
  type        = number
  description = "HTTPS listener port for the ALB."
  default     = 443
}

# ACM certificate ARN that the ALB uses to terminate TLS. Leave null to keep HTTP only.
variable "https_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS termination."
  default     = null
}

# SSL policy applied to the HTTPS listener when TLS is enabled.
variable "https_ssl_policy" {
  type        = string
  description = "SSL policy for the HTTPS listener."
  default     = "ELBSecurityPolicy-2016-08"
}

# When true and HTTPS is enabled, the HTTP listener redirects traffic to HTTPS.
variable "redirect_http_to_https" {
  type        = bool
  description = "Redirect HTTP requests to HTTPS when TLS is enabled."
  default     = true
}

# Prevents accidental deletion of the load balancer from Terraform or the AWS console.
variable "alb_deletion_protection" {
  type        = bool
  description = "Enable deletion protection on the ALB."
  default     = false
}

# Number of days to retain application logs. Longer retention aids debugging at higher storage cost.
variable "log_retention_days" {
  type        = number
  description = "Log retention in days for CloudWatch Logs."
  default     = 14
}

# Arbitrary tags applied to every resource the module creates.
variable "tags" {
  type        = map(string)
  description = "Resource tags."
  default     = {}
}
