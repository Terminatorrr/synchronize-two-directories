import logging
import logging.config
import logging.handlers
from logging import Logger
import sys


class LoggerFactory:
    def __init__(self, log_file_name: str) -> None:
        logging.basicConfig(
            format='%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s',
            level='INFO',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.handlers.RotatingFileHandler(log_file_name)
            ]
        )

    def create_logger(self, name: str) -> Logger:
        return logging.getLogger(name)
