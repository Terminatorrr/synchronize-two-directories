import os
from argparse import ArgumentParser
from synclogger import SyncLogger
from logging import Logger


class Configuration:
    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument("source", type=str, help="path to the source folder")
        parser.add_argument("destination", type=str, help="path to the destination folder")
        parser.add_argument("seconds_between_sync", type=int, help="period of synchronization, secs")
        parser.add_argument("log_location", type=str, help="location of log")
        self.args = parser.parse_args()

        self.src_dir = self.args.source
        self.dst_dir = self.args.destination
        self.sync_frequency = self.args.seconds_between_sync
        self.log_file = self.args.log_location

    def validate(self, logger: SyncLogger) -> None:
        log = logger.create_logger(class_name="Configuration")
        if (not self._is_src_path_valid(self.src_dir, log)
                or not self._is_dst_path_valid(self.src_dir, self.dst_dir, log)
                or not self._is_scan_frequency_valid(self.sync_frequency, log)):
            raise ValueError("Invalid input")


    @staticmethod
    def _try_create_dir(path: str) -> bool:
        try:
            os.mkdir(path)
            return True
        except OSError:
            return False

    @staticmethod
    def _is_src_path_valid(path: str, log: Logger) -> bool:
        if os.path.isdir(path):
            return True
        else:
            log.error("Source directory '%s' does not exist", path)
            return False

    @staticmethod
    def _is_dst_path_valid(src_path: str, dst_path: str, log: Logger) -> bool:
        if os.path.abspath(src_path) == os.path.abspath(dst_path):
            log.error("Destination directory can not be the same as the source folder")
            return False
        if not (os.path.isdir(dst_path) or Configuration._try_create_dir(dst_path)):
            log.error("Destination directory '%s' does not exist and could not be created", dst_path)
            return False
        return True

    @staticmethod
    def _is_scan_frequency_valid(frequency: int, log: Logger) -> bool:
        if frequency > 0:
            return True
        else:
            log.error("Seconds between sync '%d' must be greater than zero", frequency)
            return False
