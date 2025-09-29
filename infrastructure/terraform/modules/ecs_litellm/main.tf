// ECS + ALB stack tailored for the LiteLLM service. Provisions logging, IAM roles,
// networking, and the Fargate service itself.

locals {
  # Assemble the container definition JSON that AWS expects when registering a task
  # definition. This keeps the main resource body clean and readable.
  container_definitions = [
    {
      name      = "litellm"
      image     = var.container_image
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      # Optional override for the container's entrypoint/command.
      command = var.container_command
      # Convert the map of environment variables into the key/value struct ECS expects.
      environment = [for k, v in var.environment : {
        name  = k
        value = v
      }]
      # Secrets are injected from SSM or Secrets Manager ARNs without exposing plaintext.
      secrets = [for secret in var.secrets : {
        name      = secret.name
        valueFrom = secret.value_from
      }]
      # Send container logs to CloudWatch Logs with a predictable stream prefix.
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ]

  # Determine whether HTTPS should be configured based on the presence of a certificate ARN.
  https_enabled = length(trimspace(coalesce(var.https_certificate_arn, ""))) > 0
}

# CloudWatch Logs group that stores container stdout/stderr with configurable retention.
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/ecs/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-logs"
  })
}

# ECS cluster that hosts the Fargate service.
resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cluster"
  })
}

# Execution role lets ECS pull container images and write logs.
resource "aws_iam_role" "execution" {
  name = "${var.name_prefix}-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

# Attach AWS-managed policy that grants ECR pull, CloudWatch, and Secrets access for execution role.
resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional execution role permissions to read secrets from SSM/Secrets Manager.
resource "aws_iam_role_policy" "execution_secrets" {
  count = length(var.secret_arns) > 0 ? 1 : 0
  name  = "${var.name_prefix}-execution-secrets"
  role  = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
        Resource = var.secret_arns
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParameterHistory"],
        Resource = var.secret_arns
      }
    ]
  })
}

# Task role is assumed by the running container and should hold only the permissions the app needs.
resource "aws_iam_role" "task" {
  name = "${var.name_prefix}-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

# Grant the task role permission to fetch runtime secrets.
resource "aws_iam_role_policy" "task_secrets" {
  count = length(var.secret_arns) > 0 ? 1 : 0
  name  = "${var.name_prefix}-secrets"
  role  = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParameterHistory"],
        Resource = var.secret_arns
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
        Resource = var.secret_arns
      }
    ]
  })
}

# Application Load Balancer that fronts the service.
resource "aws_lb" "this" {
  name                       = "${var.name_prefix}-alb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb.id]
  subnets                    = var.alb_subnet_ids
  enable_deletion_protection = var.alb_deletion_protection
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb"
  })
}

# Security group that limits inbound traffic to the ALB.
resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-alb-sg"
  description = "ALB security group"
  vpc_id      = var.vpc_id
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
  })
}

# Allow incoming requests from the specified CIDR ranges to the ALB listener port.
resource "aws_security_group_rule" "alb_ingress" {
  for_each = toset(var.alb_ingress_cidrs)

  security_group_id = aws_security_group.alb.id
  type              = "ingress"
  from_port         = var.listener_port
  to_port           = var.listener_port
  protocol          = "tcp"
  cidr_blocks       = [each.value]
}

# Allow HTTPS traffic when a TLS listener is configured.
resource "aws_security_group_rule" "alb_ingress_https" {
  for_each = local.https_enabled ? toset(var.alb_ingress_cidrs) : toset([])

  security_group_id = aws_security_group.alb.id
  type              = "ingress"
  from_port         = var.https_listener_port
  to_port           = var.https_listener_port
  protocol          = "tcp"
  cidr_blocks       = [each.value]
}

# Permit the ALB to reach external services (e.g. for health checks on public endpoints).
resource "aws_security_group_rule" "alb_egress" {
  security_group_id = aws_security_group.alb.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
}

# Security group applied to ECS tasks; only allows traffic from the ALB on the app port.
resource "aws_security_group" "service" {
  name        = "${var.name_prefix}-svc-sg"
  description = "Service security group"
  vpc_id      = var.vpc_id
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-svc-sg"
  })
}

# Permit the ALB to reach the service tasks on the container port.
resource "aws_security_group_rule" "service_ingress_alb" {
  security_group_id        = aws_security_group.service.id
  type                     = "ingress"
  from_port                = var.container_port
  to_port                  = var.container_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}

# Allow outbound traffic from the service tasks so they can reach other AWS services.
resource "aws_security_group_rule" "service_egress" {
  security_group_id = aws_security_group.service.id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
}

# Task definition ties together container image, resources, IAM roles, and logging.
resource "aws_ecs_task_definition" "this" {
  family                   = "${var.name_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions    = jsonencode(local.container_definitions)
  tags                     = var.tags
}

# Target group that registers the ECS tasks and performs health checks.
resource "aws_lb_target_group" "this" {
  name        = "${var.name_prefix}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id
  health_check {
    path                = var.health_check_path
    healthy_threshold   = 3
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200-399"
  }
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-tg"
  })
}

# Listener that forwards HTTP traffic when HTTPS redirection is disabled.
resource "aws_lb_listener" "http" {
  count             = local.https_enabled && var.redirect_http_to_https ? 0 : 1
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# Listener that redirects HTTP to HTTPS when TLS is enabled and redirects are requested.
resource "aws_lb_listener" "http_redirect" {
  count             = local.https_enabled && var.redirect_http_to_https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = tostring(var.https_listener_port)
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS listener that forwards traffic to the same target group when TLS is enabled.
resource "aws_lb_listener" "https" {
  count             = local.https_enabled ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = var.https_listener_port
  protocol          = "HTTPS"
  ssl_policy        = var.https_ssl_policy
  certificate_arn   = var.https_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# ECS service keeps the desired number of tasks running and wires them to the ALB.
resource "aws_ecs_service" "this" {
  name                               = "${var.name_prefix}-svc"
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.this.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = concat([aws_security_group.service.id], var.additional_service_security_groups)
    assign_public_ip = var.assign_public_ip
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "litellm"
    container_port   = var.container_port
  }
  lifecycle {
    # Ignore desired_count drift so external autoscalers can adjust capacity.
    ignore_changes = [desired_count]
  }
  tags = var.tags
}
