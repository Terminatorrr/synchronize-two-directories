from sync import Syncer
import time
from configuration import Configuration
from synclogger import SyncLogger


def main():
    config = Configuration()
    logger = SyncLogger(config.log_file)
    config.validate(logger)
    syncer = Syncer(config.src_dir, config.dst_dir, logger)
    while True:
        start = time.time()
        syncer.do_work()
        before_next_sync = start + config.sync_frequency - time.time()
        if before_next_sync > 0:
            time.sleep(before_next_sync)


main()
