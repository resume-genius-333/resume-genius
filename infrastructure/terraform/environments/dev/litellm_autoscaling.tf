# Automation that keeps the LiteLLM service scaled down until traffic arrives and
# automatically shuts it off after a configurable idle window.

data "aws_caller_identity" "current" {}

locals {
  litellm_load_balancer_dimension = replace(
    module.litellm.alb_arn,
    "arn:aws:elasticloadbalancing:${var.aws_region}:${data.aws_caller_identity.current.account_id}:loadbalancer/",
    ""
  )
  litellm_autoscaler_name         = "${var.name_prefix}-${var.environment}-litellm-autoscaler"
  litellm_override_parameter_name = var.litellm_manual_control_enabled ? "/${var.name_prefix}/${var.environment}/litellm/manual_override" : null
}

# Parameter describing manual overrides for LiteLLM desired count. Lambda automation updates the
# value; Terraform seeds it once and then ignores subsequent changes to avoid drift.
resource "aws_ssm_parameter" "litellm_manual_override" {
  count = var.litellm_manual_control_enabled ? 1 : 0

  name = local.litellm_override_parameter_name
  type = "String"
  value = jsonencode({
    desired_count = 0
    expires_at    = "1970-01-01T00:00:00Z"
  })
  overwrite = true
  tags      = local.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_iam_role" "litellm_autoscaler" {
  name = "${local.litellm_autoscaler_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

# Allow the Lambda function to write logs, adjust the ECS service, and inspect ALB metrics.
resource "aws_iam_role_policy_attachment" "litellm_autoscaler_logs" {
  role       = aws_iam_role.litellm_autoscaler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "litellm_autoscaler_permissions" {
  name = "${local.litellm_autoscaler_name}-policy"
  role = aws_iam_role.litellm_autoscaler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:GetMetricStatistics", "cloudwatch:GetMetricData"]
        Resource = "*"
      }
      ], var.litellm_manual_control_enabled ? [
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:GetParameters"]
        Resource = aws_ssm_parameter.litellm_manual_override[0].arn
      }
    ] : [])
  })
}

# Package the autoscaling Lambda from the local source file.
data "archive_file" "litellm_autoscaler" {
  type        = "zip"
  source_file = "${path.module}/litellm_autoscaler.py"
  output_path = "${path.module}/litellm_autoscaler.zip"
}

data "archive_file" "litellm_manual_control" {
  count       = var.litellm_manual_control_enabled ? 1 : 0
  type        = "zip"
  source_file = "${path.module}/litellm_manual_control.py"
  output_path = "${path.module}/litellm_manual_control.zip"
}

resource "aws_lambda_function" "litellm_autoscaler" {
  function_name    = local.litellm_autoscaler_name
  role             = aws_iam_role.litellm_autoscaler.arn
  handler          = "litellm_autoscaler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.litellm_autoscaler.output_path
  source_code_hash = data.archive_file.litellm_autoscaler.output_base64sha256

  timeout = 30

  environment {
    variables = merge({
      CLUSTER_NAME            = module.litellm.cluster_name
      SERVICE_NAME            = module.litellm.service_name
      LOAD_BALANCER_DIMENSION = local.litellm_load_balancer_dimension
      KEEPALIVE_MINUTES       = tostring(var.litellm_idle_shutdown_minutes)
      ENABLE_EXECUTE_COMMAND  = var.litellm_enable_execute_command ? "true" : "false"
      }, var.litellm_manual_control_enabled && local.litellm_override_parameter_name != null ? {
      MANUAL_OVERRIDE_PARAMETER = local.litellm_override_parameter_name
    } : {})
  }

  tags = local.tags
}

# Lambda exposed via API Gateway so operators can request LiteLLM capacity for a fixed window.
resource "aws_iam_role" "litellm_manual_control" {
  count = var.litellm_manual_control_enabled ? 1 : 0
  name  = "${local.litellm_autoscaler_name}-manual-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "litellm_manual_control_logs" {
  count      = var.litellm_manual_control_enabled ? 1 : 0
  role       = aws_iam_role.litellm_manual_control[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "litellm_manual_control_permissions" {
  count = var.litellm_manual_control_enabled ? 1 : 0
  name  = "${local.litellm_autoscaler_name}-manual-policy"
  role  = aws_iam_role.litellm_manual_control[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:PutParameter", "ssm:GetParameter"]
        Resource = aws_ssm_parameter.litellm_manual_override[0].arn
      }
    ]
  })
}

resource "aws_lambda_function" "litellm_manual_control" {
  count            = var.litellm_manual_control_enabled ? 1 : 0
  function_name    = "${local.litellm_autoscaler_name}-manual"
  role             = aws_iam_role.litellm_manual_control[0].arn
  handler          = "litellm_manual_control.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.litellm_manual_control[0].output_path
  source_code_hash = data.archive_file.litellm_manual_control[0].output_base64sha256
  timeout          = 30

  environment {
    variables = {
      CLUSTER_NAME              = module.litellm.cluster_name
      SERVICE_NAME              = module.litellm.service_name
      MANUAL_OVERRIDE_PARAMETER = local.litellm_override_parameter_name
      DEFAULT_HOURS             = tostring(var.litellm_manual_override_default_hours)
    }
  }

  tags = local.tags
}

resource "aws_apigatewayv2_api" "litellm_control" {
  count         = var.litellm_manual_control_enabled ? 1 : 0
  name          = "${local.litellm_autoscaler_name}-api"
  protocol_type = "HTTP"
  tags          = local.tags
}

resource "aws_apigatewayv2_integration" "litellm_control" {
  count                  = var.litellm_manual_control_enabled ? 1 : 0
  api_id                 = aws_apigatewayv2_api.litellm_control[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.litellm_manual_control[0].invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "litellm_control" {
  count     = var.litellm_manual_control_enabled ? 1 : 0
  api_id    = aws_apigatewayv2_api.litellm_control[0].id
  route_key = "POST /litellm/override"
  target    = "integrations/${aws_apigatewayv2_integration.litellm_control[0].id}"
}

resource "aws_apigatewayv2_stage" "litellm_control" {
  count       = var.litellm_manual_control_enabled ? 1 : 0
  api_id      = aws_apigatewayv2_api.litellm_control[0].id
  name        = "prod"
  auto_deploy = true
  tags        = local.tags
}

resource "aws_lambda_permission" "allow_apigw_manual_control" {
  count         = var.litellm_manual_control_enabled ? 1 : 0
  statement_id  = "AllowAPIGatewayInvokeManualControl"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.litellm_manual_control[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.litellm_control[0].execution_arn}/*"
}

# SNS topic that receives CloudWatch alarm notifications and triggers the autoscaler.
resource "aws_sns_topic" "litellm_scale_up" {
  name = "${local.litellm_autoscaler_name}-scale-up"
  tags = local.tags
}

resource "aws_sns_topic_subscription" "litellm_scale_up_lambda" {
  topic_arn = aws_sns_topic.litellm_scale_up.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.litellm_autoscaler.arn
}

resource "aws_lambda_permission" "allow_sns_invoke" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.litellm_autoscaler.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.litellm_scale_up.arn
}

# Alarm fires on the first request in a quiet window and prompts the Lambda to start the service.
resource "aws_cloudwatch_metric_alarm" "litellm_first_request" {
  alarm_name          = "${local.litellm_autoscaler_name}-first-request"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  statistic           = "Sum"
  period              = 60
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = local.litellm_load_balancer_dimension
  }

  alarm_actions = [aws_sns_topic.litellm_scale_up.arn]
  ok_actions    = []
  tags          = local.tags
}

# Scheduled check that evaluates whether the service has been idle longer than the keepalive window.
resource "aws_cloudwatch_event_rule" "litellm_idle_watchdog" {
  name                = "${local.litellm_autoscaler_name}-idle-check"
  schedule_expression = "rate(${var.litellm_idle_check_interval_minutes} minutes)"
}

resource "aws_cloudwatch_event_target" "litellm_idle_watchdog_lambda" {
  rule      = aws_cloudwatch_event_rule.litellm_idle_watchdog.name
  target_id = "litellm-autoscaler"
  arn       = aws_lambda_function.litellm_autoscaler.arn
  input     = jsonencode({ action = "check" })
}

resource "aws_lambda_permission" "allow_events_invoke" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.litellm_autoscaler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.litellm_idle_watchdog.arn
}
