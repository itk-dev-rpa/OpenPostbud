"""Unit tests for OpenPostbud.

Importing this package prepares a minimal fake configuration environment so the
application modules can be imported without a real .env file present (e.g. in
CI). OpenPostbud.config loads settings from a .env file on import, and
encrypted_string.py builds a Fernet cipher from database_storage_secret at
import time, so a valid key must be available.
"""

import atexit
import os
import tempfile

from cryptography.fernet import Fernet


def _prepare_test_environment():
    """Populate env vars and placeholder files so OpenPostbud.config can be
    imported without a real .env file.

    Values are set with setdefault and an empty .env placeholder is only created
    when one is absent, so a developer's real .env is left untouched.
    """
    test_env = {
        "nicegui_storage_secret": "test-secret",
        # Must be a valid Fernet key; a cipher is built from it on import.
        "database_storage_secret": Fernet.generate_key().decode(),
        "auth_lifetime_seconds": "43200",
        "shipment_lifetime_days": "30",
        "registration_job_lifetime_days": "14",
        "api_jwt_secret": "test-secret",
        "api_token_lifetime_seconds": "3600",
        "cvr": "12345678",
        "Kombit_test_env": "True",
        "registration_worker_sleep_time": "10",
        "shipment_worker_sleep_time": "10",
        "sender_label": "Test",
        "physical_mail_forsendelse_type": "12345",
        "message_broker_queue_id": "00000000-0000-0000-0000-000000000000",
        "message_broker_worker_sleep_time": "60",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "discovery_url": "https://example.test/.well-known/openid-configuration",
        "redirect_url": "https://example.test/auth/callback",
        "jwt_leeway": "60",
        "admin_role_name": "Administrator",
        "user_role_name": "User",
    }

    # config validates that kombit_cert_path points to an existing file.
    cert_fd, cert_path = tempfile.mkstemp(prefix="test_cert_", suffix=".pem")
    os.close(cert_fd)
    atexit.register(os.unlink, cert_path)
    test_env["kombit_cert_path"] = cert_path

    for key, value in test_env.items():
        os.environ.setdefault(key, value)

    # config requires a .env file to exist (read with override=True). When one is
    # absent (e.g. in CI), create an empty placeholder so the os.environ values
    # above are used as-is.
    if not os.path.isfile(".env"):
        with open(".env", "w", encoding="utf-8"):
            pass
        atexit.register(os.unlink, ".env")


_prepare_test_environment()
