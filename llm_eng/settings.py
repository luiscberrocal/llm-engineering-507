import logging
import os

from dotenv import load_dotenv

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "level": "DEBUG",
            "filename": "module.log",
        },
    },
    "loggers": {
        "__main__": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

IMAGE_LIST = [
    {
        "name": "python",
        "image_filter": r"3\.1\d+\.\d+-([a-zA-Z]+)(-[a-zA-Z0-9]+)?",
    },
    {
        "name": "postgres",
        "image_filter": r"1[679]\.\d+-([a-zA-Z]+)(-[a-zA-Z0-9]+)?",
    },
    {
        "name": "node",
        "image_filter": r"(\d+\.\d+\.\d+)-([A-Za-z-0-9\.]+)",
    },
]

load_dotenv(override=True)
API_KEY = os.getenv('OPENAI_API_KEY')

OLLAMA_API = "http://localhost:11434/api/chat"
HEADERS = {"Content-Type": "application/json"}
# MODEL = "llama3.2"
MODEL = "deepseek-r1:7b"

logging.config.dictConfig(LOGGING_CONFIG)
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.debug("Logging configuration is set up.")
