# @track_context("secrets.md")

import logging
import os
from functools import lru_cache
from typing import Optional

from google.cloud import secretmanager

from src.core.constants import EnvVars, Supabase
from src.core.messages import LogMessages

logger = logging.getLogger(__name__)


@lru_cache
def get_secret(secret_name: str, project_id: Optional[str] = None) -> str:
    """
    Retrieve a secret from Google Secret Manager.

    Args:
        secret_name: Name of the secret to retrieve
        project_id: GCP project ID

    Returns:
        The secret value as a string
    """
    try:
        if not project_id:
            project_id = os.environ.get(EnvVars.GCP_PROJECT_ID)
            if not project_id:
                raise ValueError(
                    "GCP_PROJECT_ID must be set when using Google Secret Manager"
                )

        logger.debug(f"Attempting to retrieve secret {secret_name} from GSM")
        client = secretmanager.SecretManagerServiceClient()
        name = Supabase.SECRET_PATH_TEMPLATE.format(
            project_id=project_id, secret_name=secret_name
        )
        response = client.access_secret_version(request={"name": name})
        logger.info(LogMessages.SECRET_RETRIEVED_GSM.format(secret_name=secret_name))
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(
            LogMessages.SECRET_ACCESS_ERROR.format(secret_name=secret_name, error=e)
        )
        return os.environ.get(secret_name, "")


def load_secrets_from_gsm() -> None:
    """Load critical secrets from Google Secret Manager into environment variables"""
    for secret_name in Supabase.REQUIRED_SECRETS:
        if secret_name not in os.environ:
            logger.info(LogMessages.FETCHING_SECRET_GSM.format(secret_name=secret_name))
            secret_value = get_secret(secret_name)
            if secret_value:
                os.environ[secret_name] = secret_value
                logger.info(
                    LogMessages.SECRET_LOADED_GSM.format(secret_name=secret_name)
                )
            else:
                logger.warning(
                    LogMessages.SECRET_EMPTY_WARNING.format(secret_name=secret_name)
                )


def should_use_gsm() -> bool:
    return os.environ.get(EnvVars.USE_GSM, "false").lower() in ("true", "1", "t")
