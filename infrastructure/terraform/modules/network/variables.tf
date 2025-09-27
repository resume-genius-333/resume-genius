# Name prefix added to every network resource. Helpful for identifying which environment a
# VPC or subnet belongs to in the AWS console.
variable "name_prefix" {
  type        = string
  description = "Prefix applied to all network resources."
}

# IPv4 range allocated to the VPC. Ensure it does not overlap with any network you might
# peer with or connect via VPN.
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

# CIDR blocks for public subnets. Leave empty if you do not need internet-facing resources.
variable "public_subnet_cidrs" {
  type        = list(string)
  description = "List of public subnet CIDR blocks."
  default     = []
}

# CIDR blocks for private subnets that host workloads without public IP addresses.
variable "private_subnet_cidrs" {
  type        = list(string)
  description = "List of private subnet CIDR blocks."
  default     = []
}

# Availability zones to distribute subnets across. Provide at least as many zones as you
# have subnet CIDRs to avoid duplication.
variable "availability_zones" {
  type        = list(string)
  description = "Availability zones to spread subnets across."
}

# Enables NAT gateway creation for outbound internet access from private subnets. Disable
# to save cost if private resources never need to reach external services.
variable "enable_nat" {
  type        = bool
  description = "Whether to provision a NAT gateway for private subnets."
  default     = true
}

# Additional resource tags applied everywhere. Use for ownership metadata or chargeback.
variable "tags" {
  type        = map(string)
  description = "Tags applied to all resources."
  default     = {}
}
