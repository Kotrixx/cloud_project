from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
import os

from fastapi import Request, Response

os.makedirs("logs", exist_ok=True)

log_handler = RotatingFileHandler(
	filename="logs/request_logs.log",
	maxBytes=10 * 1024 * 1024, # 10MB
	backupCount=10,
)
log_handler.setFormatter(
	logging.Formatter(
		fmt="[%(asctime)s] - %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(log_handler)


async def request_logger(request: Request, call_next) -> Response:
	"""
	Middleware that handles all requests and logs them
	:param request: Request object
	:param call_next: Next middleware in the chain
	:return: Response object
	"""
	body = await request.body()
	try:
		body_str = body.decode("utf-8")
		body_json = json.loads(body_str)
		body_flat = json.dumps(body_json, separators=(',', ':'))
	except UnicodeDecodeError:
		body_flat = body
		logging.error(f"Unicode error when attempting request: {request.url.path} - ")
	except json.JSONDecodeError:
		body_flat = body_str
	log_message = (
		f"[*] {datetime.now(tz=timezone.utc)} - {request.method} - {request.url.path} - {request.client.host} - "
		f"{request.headers} - {f'{request.query_params} - ' if request.query_params else ''}{body_flat}"
	)

	logging.info(log_message)
	response = await call_next(request)

	return response
