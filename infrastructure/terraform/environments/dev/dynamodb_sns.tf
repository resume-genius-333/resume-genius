// Deploys optional SNS topics controlled via environment variables so environments can
// opt-in without modifying shared code. Rename retained for compatibility with existing
// includes; only SNS logic remains.

locals {
  sns_topics = {
    for name, cfg in var.sns_topics :
    name => {
      requested_name              = try(cfg.name, null)
      display_name                = try(cfg.display_name, null)
      fifo_topic                  = try(cfg.fifo_topic, false)
      content_based_deduplication = try(cfg.content_based_deduplication, false)
      delivery_policy             = try(cfg.delivery_policy, null)
      policy                      = try(cfg.policy, null)
      kms_master_key_id           = try(cfg.kms_master_key_id, null)
      tracing_config              = try(cfg.tracing_config, null)
      subscriptions               = try(cfg.subscriptions, [])
      tags                        = try(cfg.tags, {})
    }
  }

  sns_topic_names = {
    for name, cfg in local.sns_topics :
    name => (
      cfg.fifo_topic ? (
        cfg.requested_name != null ? (
          endswith(cfg.requested_name, ".fifo") ? cfg.requested_name : "${cfg.requested_name}.fifo"
        ) : "${var.name_prefix}-${var.environment}-${name}.fifo"
      ) : coalesce(cfg.requested_name, "${var.name_prefix}-${var.environment}-${name}")
    )
  }

  sns_topic_subscriptions = {
    for subscription in flatten([
      for topic_key, cfg in local.sns_topics : [
        for idx, sub in cfg.subscriptions : {
          key                   = "${topic_key}-${idx}"
          topic_key             = topic_key
          protocol              = sub.protocol
          endpoint              = sub.endpoint
          raw_message_delivery  = try(sub.raw_message_delivery, null)
          filter_policy         = try(sub.filter_policy, null)
          filter_policy_scope   = try(sub.filter_policy_scope, null)
          redrive_policy        = try(sub.redrive_policy, null)
          delivery_policy       = try(sub.delivery_policy, null)
          subscription_role_arn = try(sub.subscription_role_arn, null)
        }
      ]
    ]) : subscription.key => subscription
  }
}

resource "aws_sns_topic" "additional" {
  for_each = local.sns_topics

  name                        = local.sns_topic_names[each.key]
  display_name                = each.value.fifo_topic ? null : each.value.display_name
  fifo_topic                  = each.value.fifo_topic
  content_based_deduplication = each.value.fifo_topic ? each.value.content_based_deduplication : null
  delivery_policy             = each.value.delivery_policy
  policy                      = each.value.policy
  kms_master_key_id           = each.value.kms_master_key_id
  tracing_config              = each.value.tracing_config

  tags = merge(local.tags, each.value.tags)
}

resource "aws_sns_topic_subscription" "additional" {
  for_each = local.sns_topic_subscriptions

  topic_arn = aws_sns_topic.additional[each.value.topic_key].arn
  protocol  = each.value.protocol
  endpoint  = each.value.endpoint

  raw_message_delivery  = each.value.raw_message_delivery
  filter_policy         = each.value.filter_policy
  filter_policy_scope   = each.value.filter_policy_scope
  redrive_policy        = each.value.redrive_policy
  delivery_policy       = each.value.delivery_policy
  subscription_role_arn = each.value.subscription_role_arn
}
