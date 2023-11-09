import os
import time
import shutil
import filecmp
from loggerfactory import LoggerFactory


class ComparisonResults:
    def __init__(self, left_folders: set, right_folders: set, left_files: set, right_files: set, common_files: set):
        self.left_folders = left_folders
        self.right_folders = right_folders
        self.left_files = left_files
        self.right_files = right_files
        self.common_files = common_files


class SyncStatistics:
    def __init__(self):
        self.num_dirs = 0
        self.num_files = 0
        self.num_del_files = 0
        self.num_del_dirs = 0
        self.num_new_dirs = 0
        self.num_content_updates = 0

        # failure stat vars
        self.num_copy_fld = 0
        self.num_updates_fld = 0
        self.num_del_file_fld = 0
        self.num_del_dir_fld = 0

        self.start_time = 0.0
        self.end_time = 0.0


class Sync:
    def __init__(self, src_dir: str, dst_dir: str, logger: LoggerFactory) -> None:
        self.logger = logger.create_logger(__name__)

        self._src_dir = src_dir.replace("\\", "/")
        self._dst_dir = dst_dir.replace("\\", "/")

        if not os.path.isdir(self._src_dir):
            raise ValueError("Error: Source directory does not exist.")

    def log(self, msg: str = "") -> None:
        self.logger.info(msg)

    def _compare(self, sync_statistics: SyncStatistics) -> ComparisonResults:
        sync_statistics.num_dirs += 1

        (left_folders, left_files) = self._scan_dir(
            self._src_dir, sync_statistics)
        (right_folders, right_files) = self._scan_dir(self._dst_dir)

        common_folders = left_folders.intersection(right_folders)
        common_files = left_files.intersection(right_files)
        left_folders.difference_update(common_folders)
        right_folders.difference_update(common_folders)
        left_files.difference_update(common_files)
        right_files.difference_update(common_files)

        return ComparisonResults(left_folders, right_folders, left_files, right_files, common_files)

    def synchronize(self) -> None:
        sync_statistics = SyncStatistics()
        sync_statistics.start_time = time.time()

        self.log("Synchronizing directory %s with %s" %
                 (self._dst_dir, self._src_dir))

        comparison_results = self._compare(sync_statistics)

        # Files & directories only in target directory
        self._del_right_files(comparison_results, sync_statistics)
        self._del_right_folders(comparison_results, sync_statistics)

        # Files & directories only in source directory
        for f1 in comparison_results.left_folders:
            to_make = os.path.join(self._dst_dir, f1).replace("\\", "/")
            if not os.path.exists(to_make):
                try:
                    os.makedirs(to_make)
                    sync_statistics.num_new_dirs += 1
                except FileNotFoundError as e:
                    self.log(str(e))
        for f1 in comparison_results.left_files:
            self._copy(f1, self._src_dir, self._dst_dir, sync_statistics)

        # common files
        for f1 in comparison_results.common_files:
            self._update(f1, self._src_dir, self._dst_dir, sync_statistics)

        sync_statistics.end_time = time.time()
        self._report(sync_statistics)

    def _del_right_folders(self, comparison_results: ComparisonResults, sync_statistics: SyncStatistics) -> None:
        for f2 in comparison_results.right_folders:
            fullf2 = os.path.join(self._dst_dir, f2).replace("\\", "/")
            self.log("Deleting %s" % fullf2)
            try:
                shutil.rmtree(fullf2, True)
                sync_statistics.num_del_dirs += 1
            except Exception as e:
                self.log(str(e))
                sync_statistics.num_del_dir_fld += 1

    def _del_right_files(self, comparison_results: ComparisonResults, sync_statistics: SyncStatistics) -> None:
        for f2 in comparison_results.right_files:
            fullf2 = os.path.join(self._dst_dir, f2).replace("\\", "/")
            self.log("Deleting %s" % fullf2)
            try:
                os.remove(fullf2)
                sync_statistics.num_del_files += 1
            except Exception as e:
                self.log(str(e))
                sync_statistics.num_del_file_fld += 1

    def _copy(self, file_name: str, src_dir: str, dst_dir: str, sync_statistics: SyncStatistics) -> None:
        rel_path = file_name.replace("\\", "/").split("/")
        rel_dir = "/".join(rel_path[:-1])
        file_name = rel_path[-1]

        src_dir = os.path.join(src_dir, rel_dir).replace("\\", "/")
        dst_dir = os.path.join(dst_dir, rel_dir).replace("\\", "/")

        self.log("Copying file %s from %s to %s" %
                 (file_name, src_dir, dst_dir))

        try:
            sourcefile = os.path.join(src_dir, file_name).replace("\\", "/")
            try:
                shutil.copy2(sourcefile, dst_dir)
                sync_statistics.num_files += 1
            except (IOError, OSError) as e:
                self.log(str(e))
                sync_statistics.num_copy_fld += 1
        except Exception as e:
            self.log("Error copying file %s" % file_name)
            self.log(str(e))

    def _update(self, file_name: str, src_dir: str, dst_dir: str, sync_statistics: SyncStatistics) -> None:
        file1 = os.path.join(src_dir, file_name).replace("\\", "/")
        file2 = os.path.join(dst_dir, file_name).replace("\\", "/")

        if not filecmp.cmp(file1, file2, False):
            self.log("Updating file %s" % file2)

            try:
                shutil.copy2(file1, file2)
                sync_statistics.num_content_updates += 1
            except Exception as e:
                self.log(str(e))
                sync_statistics.num_updates_fld += 1

    def _report(self, sync_statistics: SyncStatistics) -> None:
        tt = (str(sync_statistics.end_time - sync_statistics.start_time))[:4]

        self.log("Synchronization finished in %s seconds" % tt)
        self.log("%d directories parsed, %d files copied" %
                 (sync_statistics.num_dirs, sync_statistics.num_files))
        if sync_statistics.num_del_files:
            self.log("%d files were purged" % sync_statistics.num_del_files)
        if sync_statistics.num_del_dirs:
            self.log("%d directories were purged" %
                     sync_statistics.num_del_dirs)
        if sync_statistics.num_new_dirs:
            self.log("%d directories were created" %
                     sync_statistics.num_new_dirs)
        if sync_statistics.num_content_updates:
            self.log("%d files were updated by content" %
                     sync_statistics.num_content_updates)

        # Failure stats
        if sync_statistics.num_copy_fld:
            self.log("there were errors in copying %d files"
                     % sync_statistics.num_copy_fld)
        if sync_statistics.num_updates_fld:
            self.log("there were errors in updating %d files"
                     % sync_statistics.num_updates_fld)
        if sync_statistics.num_del_dir_fld:
            self.log("there were errors in purging %d directories"
                     % sync_statistics.num_del_dir_fld)
        if sync_statistics.num_del_file_fld:
            self.log("there were errors in purging %d files"
                     % sync_statistics.num_del_file_fld)

    @staticmethod
    def _scan_dir(folder: str, sync_statistics: SyncStatistics = None) -> tuple:
        dir_items = set()
        file_items = set()
        for cwd, dirs, files in os.walk(folder):
            if sync_statistics:
                sync_statistics.num_dirs += len(dirs)
            for f in dirs:
                path = os.path.relpath(os.path.join(cwd, f), folder).replace("\\", "/")
                dir_items.add(path)
            for f in files:
                path = os.path.relpath(os.path.join(cwd, f), folder).replace("\\", "/")
                file_items.add(path)
        items = (dir_items, file_items)
        return items
