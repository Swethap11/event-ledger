import json
import logging
import os


class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        return json.dumps(log_obj)


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=LOG_LEVEL, format="%(message)s")
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

json_formatter = CustomJsonFormatter()

for handler in logger.handlers:
    handler.setFormatter(json_formatter)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
