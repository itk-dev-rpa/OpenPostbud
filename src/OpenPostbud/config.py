"""This module handles loading and reading .env files.
All modules using env variables should go through here.
"""

import os
import logging

import dotenv


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(asctime)s | %(message)s", datefmt="%m/%d/%Y %H:%M:%S%z")

ENV_PATH = ".env"

if not os.path.isfile(ENV_PATH):
    raise FileNotFoundError(f"No .env file found: {ENV_PATH}")

dotenv.load_dotenv(ENV_PATH, override=True)

# App
NICEGUI_STORAGE_SECRET = os.environ['nicegui_storage_secret']
DATABASE_STORAGE_SECRET = os.environ['database_storage_secret']
AUTH_LIFETIME_SECONDS = int(os.environ['auth_lifetime_seconds'])

# Workers
CVR = os.environ['cvr']
KOMBIT_CERT_PATH = os.environ['kombit_cert_path']
KOMBIT_TEST_ENV = bool(os.environ['Kombit_test_env'])

# Registration worker
REGISTRATION_WORKER_SLEEP_TIME = float(os.environ['registration_worker_sleep_time'])

# Shipment worker
SHIPMENT_WORKER_SLEEP_TIME = float(os.environ['shipment_worker_sleep_time'])
SENDER_LABEL = os.environ['sender_label']
PATH_TO_LIBREOFFICE = os.environ['path_to_libreoffice']

# OIDC
CLIENT_ID = os.environ['client_id']
CLIENT_SECRET = os.environ['client_secret']
DISCOVERY_URL = os.environ['discovery_url']
REDIRECT_URL = os.environ['redirect_url']
JWT_LEEWAY = float(os.environ['jwt_leeway'])
ADMIN_ROLE_NAME = os.environ['admin_role_name']
USER_ROLE_NAME = os.environ['user_role_name']