import os
from argparse import ArgumentParser


class Configuration:
    def __init__(self) -> None:
        parser = ArgumentParser()
        parser.add_argument("source", type=str, help="path to the source folder")
        parser.add_argument("destination", type=str, help="path to the destination folder")
        parser.add_argument("seconds_between_sync", type=int, help="period of synchronization, secs")
        parser.add_argument("log_file", type=str, help="name of the log file")

        args = parser.parse_args()

        self.src_dir = args.source
        self.dst_dir = args.destination
        self.sync_frequency = args.seconds_between_sync
        self.log_file = args.log_file

        self._validate()

    def _validate(self) -> None:
        errors = []

        # validate src_dir
        if not os.path.isdir(self.src_dir):
            errors.append(f"Source directory '{self.src_dir}' does not exist")

        # validate dst_dir
        if os.path.abspath(self.src_dir) == os.path.abspath(self.dst_dir):
            errors.append("Destination directory can not be the same as the source folder")
        if not (os.path.isdir(self.src_dir) or Configuration._try_create_dir(self.dst_dir)):
            errors.append(f"Destination directory '{self.dst_path}' does not exist and could not be created")

        # validate frequency
        if self.sync_frequency < 1:
            errors.append(f"Seconds between sync must be greater than zero, current value is '{self.sync_frequency}'")

        if len(errors) > 0:
            raise ValueError(errors)

    @staticmethod
    def _try_create_dir(path: str) -> bool:
        try:
            os.mkdir(path)
            return True
        except OSError:
            return False
