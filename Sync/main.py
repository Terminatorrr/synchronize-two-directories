from sync import Sync
import time
from configuration import Configuration
from loggerfactory import LoggerFactory


def main():
    config = Configuration()
    logger_factory = LoggerFactory(config.log_file)
    logger = logger_factory.create_logger(__name__)
    logger.info("Initializing synchronization")
    syncer = Sync(config.src_dir, config.dst_dir, logger_factory)
    try:
        while True:
            start = time.time()
            syncer.synchronize()
            before_next_sync = start + config.sync_frequency - time.time()
            if before_next_sync > 0:
                time.sleep(before_next_sync)
    except KeyboardInterrupt:
        logger.info("Synchronization stopped")


if __name__ == "__main__":
    main()
