// Creates the core networking primitives (VPC, subnets, routing) used by higher-level
// modules. Designed to support both public-facing and private-only workloads.

# Virtual Private Cloud that encapsulates all networking resources. DNS support is enabled
# so instances can resolve internal hostnames and register private DNS records.
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
  })
}

# Internet gateway provides a route from public subnets to the wider internet.
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
  })
}

# Public subnets host load balancers or other resources that need public IP addresses.
resource "aws_subnet" "public" {
  for_each   = { for idx, cidr in var.public_subnet_cidrs : idx => cidr }
  vpc_id     = aws_vpc.this.id
  cidr_block = each.value
  # Enable automatic public IP assignment for resources launched here.
  map_public_ip_on_launch = true
  # Cycle through the provided availability zones to distribute subnets across AZs.
  availability_zone = element(var.availability_zones, each.key % length(var.availability_zones))
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-${each.key}"
    Tier = "public"
  })
}

# Private subnets house application services and databases that should remain internal.
resource "aws_subnet" "private" {
  for_each          = { for idx, cidr in var.private_subnet_cidrs : idx => cidr }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = element(var.availability_zones, each.key % length(var.availability_zones))
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-${each.key}"
    Tier = "private"
  })
}

# Route table that sends internet-bound traffic from public subnets through the internet gateway.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public"
  })
}

# Default route enabling internet access for public subnets.
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

# Attach each public subnet to the public route table.
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# Elastic IP reserved for the NAT gateway. Created only when NAT is enabled to avoid cost.
resource "aws_eip" "nat" {
  count      = var.enable_nat ? 1 : 0
  domain     = "vpc"
  depends_on = [aws_internet_gateway.this]
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat"
  })
}

# NAT gateway that lets private subnets reach the internet without exposing inbound traffic.
resource "aws_nat_gateway" "this" {
  count         = var.enable_nat ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = values(aws_subnet.public)[0].id
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat"
  })
}

# Private route table directs outbound traffic either to the NAT gateway or remains empty
# when no private subnets are defined.
resource "aws_route_table" "private" {
  count  = length(aws_subnet.private) > 0 ? 1 : 0
  vpc_id = aws_vpc.this.id
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private"
  })
}

# Private subnets route their non-local traffic through the NAT gateway when enabled.
resource "aws_route" "private_nat" {
  count                  = var.enable_nat && length(aws_route_table.private) > 0 ? 1 : 0
  route_table_id         = aws_route_table.private[0].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[0].id
}

# Associate private subnets with the private route table if one exists.
resource "aws_route_table_association" "private" {
  for_each       = aws_route_table.private == [] ? {} : aws_subnet.private
  subnet_id      = each.value.id
  route_table_id = aws_route_table.private[0].id
}
