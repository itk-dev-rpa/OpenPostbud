"""This module handles loading and reading .env files.
All modules using env variables should go through here.
"""

import os
import logging
import json

import dotenv


def str_to_bool(s: str) -> bool:
    """Convert a true/false string to a boolean value."""
    if s.lower() not in ("true", "false"):
        raise ValueError(f"Invalid boolean value: {s}")

    return s.lower() == "true"


# Set logging options for all processes
class JsonLogger(logging.Formatter):
    """A custom log formatter which outputs json strings."""
    def format(self, record: logging.LogRecord):
        message = {
            "log_time": self.formatTime(record, self.datefmt),
            "level_name": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(message)


handler = logging.StreamHandler()
handler.setFormatter(JsonLogger())
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Load .env file
ENV_PATH = ".env"

if not os.path.isfile(ENV_PATH):
    raise FileNotFoundError(f"No .env file found: {ENV_PATH}")

dotenv.load_dotenv(ENV_PATH, override=True)

# App
APP_RELOAD = str_to_bool(os.getenv("app_reload", "False"))
NICEGUI_STORAGE_SECRET = os.environ['nicegui_storage_secret']
DATABASE_STORAGE_SECRET = os.environ['database_storage_secret']
AUTH_LIFETIME_SECONDS = int(os.environ['auth_lifetime_seconds'])
SHIPMENT_LIFETIME_DAYS = int(os.environ['shipment_lifetime_days'])
REGISTRATION_JOB_LIFETIME_DAYS = int(os.environ['registration_job_lifetime_days'])

# Workers
CVR = os.environ['cvr']
KOMBIT_CERT_PATH = os.environ['kombit_cert_path']
if not os.path.isfile(KOMBIT_CERT_PATH):
    raise ValueError(f"Couldn't find certificate file: {KOMBIT_CERT_PATH}")
KOMBIT_TEST_ENV = str_to_bool(os.environ['Kombit_test_env'])

# Registration worker
REGISTRATION_WORKER_SLEEP_TIME = float(os.environ['registration_worker_sleep_time'])

# Shipment worker
SHIPMENT_WORKER_SLEEP_TIME = float(os.environ['shipment_worker_sleep_time'])
SENDER_LABEL = os.environ['sender_label']
SHIPMENT_WORKER_DELAY = int(os.getenv("shipment_worker_delay", "300"))

# Message broker worker
MESSAGE_BROKER_QUEUE_ID = os.environ['message_broker_queue_id']
MESSAGE_BROKER_WORKER_SLEEP_TIME = float(os.environ['message_broker_worker_sleep_time'])

# OIDC
CLIENT_ID = os.environ['client_id']
CLIENT_SECRET = os.environ['client_secret']
DISCOVERY_URL = os.environ['discovery_url']
REDIRECT_URL = os.environ['redirect_url']
JWT_LEEWAY = float(os.environ['jwt_leeway'])
ADMIN_ROLE_NAME = os.environ['admin_role_name']
USER_ROLE_NAME = os.environ['user_role_name']
