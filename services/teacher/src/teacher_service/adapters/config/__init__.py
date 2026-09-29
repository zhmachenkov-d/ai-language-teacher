"""Config and secrets adapter (OS app-data layout)."""

from teacher_service.adapters.config.layout import (
    APP_AUTHOR,
    APP_NAME,
    DATA_DIR_ENV,
    SECRET_BEARER_TOKEN,
    SECRET_CLOUD_VOICE_API_KEY,
    SECRET_LLM_API_KEY,
    SECRET_TELEGRAM_BOT_TOKEN,
    FileConfig,
    resolve_data_dir,
)

__all__ = [
    "APP_AUTHOR",
    "APP_NAME",
    "DATA_DIR_ENV",
    "SECRET_BEARER_TOKEN",
    "SECRET_CLOUD_VOICE_API_KEY",
    "SECRET_LLM_API_KEY",
    "SECRET_TELEGRAM_BOT_TOKEN",
    "FileConfig",
    "resolve_data_dir",
]
