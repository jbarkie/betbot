"""JSON events for measuring serving latency and pitcher-feature provenance."""

from datetime import datetime, timezone
import json
import logging

# Emit INFO events even under Uvicorn's default logging configuration. Keep a
# dedicated handler so root handlers do not duplicate events or drop INFO logs.
logger = logging.getLogger('betbot.pitcher')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
logger.propagate = False


def record_event(event, **fields):
    logger.info(json.dumps({
        'event': event,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **fields,
    }, sort_keys=True))
