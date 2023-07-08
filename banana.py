import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default_formatter": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "default_formatter",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["stream_handler"],
        "level": "INFO",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

assets = ["aapl", "msft"]
tcs = [0.0, 0.0025]
logger.info("### Routine option selected ###")
logger.info(f"------- Routine Summary ------- {assets}")
logger.info(f"Assets: {assets}, Transaction Costs: {tcs}")
logger.info(f"Transaction Costs: {tcs}")


