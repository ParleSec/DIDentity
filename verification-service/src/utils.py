import logging

logger = logging.getLogger(__name__)

def log_request_info(method: str, path: str):
    logger.info(f"Received {method} request to {path}")