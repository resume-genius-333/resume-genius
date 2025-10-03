import json
import logging
import os
from datetime import datetime, timedelta, timezone

from boto3.session import Session

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger.setLevel(logging.INFO)

CLUSTER_NAME = os.environ["CLUSTER_NAME"]
SERVICE_NAME = os.environ["SERVICE_NAME"]
MANUAL_OVERRIDE_PARAMETER = os.environ["MANUAL_OVERRIDE_PARAMETER"]
DEFAULT_HOURS = float(os.environ.get("DEFAULT_HOURS", "2"))

_session = Session()
REGION = os.environ.get("AWS_REGION", _session.region_name)
if REGION is None:
    raise RuntimeError("Unable to determine AWS region for LiteLLM manual control Lambda")

ecs = _session.client("ecs", region_name=REGION)
ssm = _session.client("ssm", region_name=REGION)


def _json_response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _parse_hours(event: dict):
    hours = DEFAULT_HOURS
    action = "activate"

    params = event.get("queryStringParameters") or {}
    if "hours" in params and params["hours"] is not None:
        try:
            hours = float(params["hours"])
        except ValueError:
            pass
    if "action" in params and params["action"]:
        action = params["action"]

    body_data = {}
    if event.get("body"):
        try:
            body_data = json.loads(event["body"] or "{}")
        except json.JSONDecodeError:
            body_data = {}
        if "hours" in body_data:
            try:
                hours = float(body_data["hours"])
            except (TypeError, ValueError):
                pass
        if "action" in body_data and body_data["action"]:
            action = body_data["action"]

    return hours, action


def _put_override(desired_count: int, hours: float) -> tuple[int, str]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=hours)
    payload = {
        "desired_count": desired_count,
        "expires_at": expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    ssm.put_parameter(
        Name=MANUAL_OVERRIDE_PARAMETER,
        Value=json.dumps(payload),
        Type="String",
        Overwrite=True,
    )
    logger.info("Updated manual override parameter: %s", payload)
    return desired_count, payload["expires_at"]


def handler(event, _context):
    logger.info("Manual control invoked with event: %s", json.dumps(event))
    hours, action = _parse_hours(event)

    if action == "deactivate":
        _put_override(0, -1)
        ecs.update_service(cluster=CLUSTER_NAME, service=SERVICE_NAME, desiredCount=0)
        return _json_response(200, {"status": "deactivated"})

    if hours <= 0:
        hours = DEFAULT_HOURS

    desired_count, expires_at = _put_override(1, hours)
    ecs.update_service(cluster=CLUSTER_NAME, service=SERVICE_NAME, desiredCount=desired_count)

    return _json_response(
        200,
        {
            "status": "activated",
            "desired_count": desired_count,
            "override_expires_at": expires_at,
        },
    )
