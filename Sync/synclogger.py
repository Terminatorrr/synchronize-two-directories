import logging
from logging import Logger


class SyncLogger:

    def __init__(self, log_file: str):
        self.log_file = log_file

    def create_logger(self, class_name) -> Logger:
        log = logging.getLogger(class_name)
        log.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch2 = logging.FileHandler(self.log_file)

        formatter = logging.Formatter('%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s')

        ch.setFormatter(formatter)
        ch2.setFormatter(formatter)

        log.addHandler(ch)
        log.addHandler(ch2)

        return log
