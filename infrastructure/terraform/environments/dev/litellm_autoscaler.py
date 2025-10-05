import json
import os
import logging
from datetime import datetime, timedelta, timezone

from boto3.session import Session

def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    logger.setLevel(logging.INFO)
    return logger

ECS_CLUSTER = os.environ["CLUSTER_NAME"]
ECS_SERVICE = os.environ["SERVICE_NAME"]
LOAD_BALANCER_DIMENSION = os.environ["LOAD_BALANCER_DIMENSION"]
KEEPALIVE_MINUTES = int(os.environ["KEEPALIVE_MINUTES"])
MANUAL_OVERRIDE_PARAMETER = os.environ.get("MANUAL_OVERRIDE_PARAMETER")
ENABLE_EXECUTE_COMMAND = os.environ.get("ENABLE_EXECUTE_COMMAND", "false").lower() == "true"

session = Session()
REGION = os.environ.get("AWS_REGION", session.region_name)
if REGION is None:
    raise RuntimeError("AWS region not resolved for LiteLLM autoscaler Lambda")
ecs = session.client("ecs", region_name=REGION)
cloudwatch = session.client("cloudwatch", region_name=REGION)
ssm = session.client("ssm", region_name=REGION)

logger = _configure_logger()


def _scale_service(desired_count: int) -> None:
    logger.info("Scaling ECS service '%s' to desired count %s", ECS_SERVICE, desired_count)
    ecs.update_service(cluster=ECS_CLUSTER, service=ECS_SERVICE, desiredCount=desired_count)


def _current_service_desired_count() -> int:
    response = ecs.describe_services(cluster=ECS_CLUSTER, services=[ECS_SERVICE])
    services = response.get("services", [])
    if not services:
        return 0
    desired = services[0].get("desiredCount", 0)
    logger.debug("Current desired count for service '%s' is %s", ECS_SERVICE, desired)
    return desired


def _recent_request_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=KEEPALIVE_MINUTES)


def _last_request_time(window_end: datetime) -> datetime | None:
    window_start = window_end - timedelta(minutes=KEEPALIVE_MINUTES)
    metric = cloudwatch.get_metric_statistics(
        Namespace="AWS/ApplicationELB",
        MetricName="RequestCount",
        Dimensions=[{"Name": "LoadBalancer", "Value": LOAD_BALANCER_DIMENSION}],
        StartTime=window_start,
        EndTime=window_end,
        Period=60,
        Statistics=["Sum"],
    )
    datapoints = metric.get("Datapoints", [])
    recent = [dp for dp in datapoints if dp.get("Sum", 0) > 0]
    if not recent:
        logger.info(
            "No ALB requests detected between %s and %s (keepalive=%s minutes)",
            window_start.isoformat(),
            window_end.isoformat(),
            KEEPALIVE_MINUTES,
        )
        return None
    latest = max(dp["Timestamp"] for dp in recent)
    logger.info("Last ALB request observed at %s", latest.isoformat())
    return latest


def _handle_scale_up() -> None:
    now = datetime.now(timezone.utc)
    minimum_running = max(1, _manual_override_floor(now))
    if ENABLE_EXECUTE_COMMAND:
        minimum_running = max(minimum_running, 1)
    if _current_service_desired_count() >= minimum_running:
        logger.info("Scale-up request ignored; service already running")
        return
    logger.info("Scale-up triggered after incoming traffic")
    _scale_service(minimum_running)


def _handle_idle_check() -> None:
    now = datetime.now(timezone.utc)
    override_floor = _manual_override_floor(now)
    if ENABLE_EXECUTE_COMMAND and override_floor > 0:
        override_floor = max(override_floor, 1)

    current_desired = _current_service_desired_count()
    if current_desired < override_floor:
        logger.info(
            "Service desired count %s below override floor %s; bumping up",
            current_desired,
            override_floor,
        )
        _scale_service(override_floor)
        current_desired = override_floor

    last_request = _last_request_time(now)
    if last_request and last_request >= _recent_request_cutoff():
        if current_desired < max(1, override_floor):
            logger.info("Recent traffic found; restarting service")
            _scale_service(max(1, override_floor, 1))
        return

    if current_desired > override_floor:
        logger.info("Idle window exceeded; scaling service down to override floor %s", override_floor)
        _scale_service(override_floor)
    else:
        logger.info("Service already at override floor %s; nothing to do", override_floor)


def _manual_override_floor(now: datetime) -> int:
    if not MANUAL_OVERRIDE_PARAMETER:
        return 0

    try:
        response = ssm.get_parameter(Name=MANUAL_OVERRIDE_PARAMETER)
    except ssm.exceptions.ParameterNotFound:
        return 0
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to read manual override parameter")
        return 0

    try:
        payload = json.loads(response["Parameter"]["Value"])
    except (KeyError, json.JSONDecodeError):
        logger.warning("Manual override parameter has invalid payload")
        return 0

    try:
        expires_raw = payload.get("expires_at")
        if not expires_raw:
            return 0
        expires_at = datetime.fromisoformat(expires_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        logger.warning("Invalid expires_at in manual override parameter: %s", payload)
        return 0

    if expires_at <= now:
        return 0

    desired = payload.get("desired_count", 0)
    try:
        desired_int = int(desired)
    except (TypeError, ValueError):
        logger.warning("Invalid desired_count in manual override parameter: %s", payload)
        return 0

    return max(desired_int, 0)


def handler(event, _context):
    try:
        logger.info("Autoscaler invoked with event: %s", json.dumps(event))
    except (TypeError, ValueError):
        logger.info("Autoscaler invoked with non-serialisable event")
    if "Records" in event:
        # SNS notifications wrap the CloudWatch alarm payload in the Sns message body.
        for record in event["Records"]:
            message = record.get("Sns", {}).get("Message")
            if not message:
                continue
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                continue
            if payload.get("NewStateValue") == "ALARM":
                logger.info("Received ALB traffic alarm; processing scale-up")
                _handle_scale_up()
        return {"status": "scale-up-processed"}

    action = event.get("action")
    if action == "check" or event.get("source") == "aws.events":
        logger.info("Running scheduled idle check")
        _handle_idle_check()
        return {"status": "idle-check-processed"}

    return {"status": "ignored"}
