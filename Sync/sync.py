import os
import time
import shutil
import filecmp
from synclogger import SyncLogger


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


class Syncer:
    """ An advanced directory synchronisation, update
    and file copying class """

    def __init__(self, src_dir: str, dst_dir: str, logger: SyncLogger):
        self.logger = logger.create_logger("Syncer")

        self._src_dir = src_dir
        self._dst_dir = dst_dir

        if not os.path.isdir(self._src_dir):
            raise ValueError("Error: Source directory does not exist.")

    def log(self, msg: str = '') -> None:
        self.logger.info(msg)

    """ Compare contents of two directories """
    def _compare(self, sync_statistics: SyncStatistics) -> ComparisonResults:
        sync_statistics.num_dirs += 1

        (left_folders, left_files) = self._scan_dir(self._src_dir, sync_statistics)
        (right_folders, right_files) = self._scan_dir(self._dst_dir)

        common_folders = left_folders.intersection(right_folders)
        common_files = left_files.intersection(right_files)
        left_folders.difference_update(common_folders)
        right_folders.difference_update(common_folders)
        left_files.difference_update(common_files)
        right_files.difference_update(common_files)
        return ComparisonResults(left_folders, right_folders, left_files, right_files, common_files)

    def do_work(self) -> None:
        sync_statistics = SyncStatistics()
        sync_statistics.start_time = time.time()

        self.log('Synchronizing directory %s with %s' % (self._dst_dir, self._src_dir))
        self.log('Source directory: %s:' % self._src_dir)

        comparison_results = self._compare(sync_statistics)

        # Files & directories only in target directory
        self._del_right_files(comparison_results, sync_statistics)
        self._del_right_folders(comparison_results, sync_statistics)

        # Files & directories only in source directory
        for f1 in comparison_results.left_folders:
            to_make = os.path.join(self._dst_dir, f1)
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
            fullf2 = os.path.join(self._dst_dir, f2)
            self.log('Deleting %s' % fullf2)
            try:
                shutil.rmtree(fullf2, True)
                sync_statistics.num_del_dirs += 1
            except Exception as e:
                self.log(str(e))
                sync_statistics.num_del_dir_fld += 1

    def _del_right_files(self, comparison_results: ComparisonResults, sync_statistics: SyncStatistics) -> None:
        for f2 in comparison_results.right_files:
            fullf2 = os.path.join(self._dst_dir, f2)
            self.log('Deleting %s' % fullf2)
            try:
                os.remove(fullf2)
                sync_statistics.num_del_files += 1
            except Exception as e:
                self.log(str(e))
                sync_statistics.num_del_file_fld += 1

    """ Private function for copying a file """
    def _copy(self, filename: str, src_file: str, dst_file: str, sync_statistics: SyncStatistics) -> None:
        rel_path = filename.replace('\\', '/').split('/')
        rel_dir = '/'.join(rel_path[:-1])
        filename = rel_path[-1]

        src_file = os.path.join(src_file, rel_dir).replace("\\","/")
        dst_file = os.path.join(dst_file, rel_dir).replace("\\","/")

        self.log('Copying file %s from %s to %s' %
                 (filename, src_file, dst_file))

        try:
            # source to target
            sourcefile = os.path.join(src_file, filename)
            try:
                shutil.copy2(sourcefile, dst_file)
                sync_statistics.num_files += 1
            except (IOError, OSError) as e:
                self.log(str(e))
                sync_statistics.num_copy_fld += 1
        except Exception as e:
            self.log('Error copying file %s' % filename)
            self.log(str(e))

    """ Private function for updating a file based on difference of content"""
    def _update(self, filename: str, src_dir: str, dst_dir: str, sync_statistics: SyncStatistics) -> None:
        file1 = os.path.join(src_dir, filename)
        file2 = os.path.join(dst_dir, filename)

        # Update will update in dst directory depending
        # on the file size and its content.

        if not filecmp.cmp(file1, file2, False):
            # source to target
            self.log('Updating file %s' % file2)

            try:
                shutil.copy2(file1, file2)
                sync_statistics.num_content_updates += 1
            except Exception as e:
                self.log(str(e))
                sync_statistics.num_updates_fld += 1

    """ Print report of work at the end """
    def _report(self, sync_statistics: SyncStatistics) -> None:
        # We need only the first 4 significant digits
        tt = (str(sync_statistics.end_time - sync_statistics.start_time))[:4]

        self.log('Synchronization finished in %s seconds.' % tt)
        self.log('%d directories parsed, %d files copied' %
                 (sync_statistics.num_dirs, sync_statistics.num_files))
        if sync_statistics.num_del_files:
            self.log('%d files were purged.' % sync_statistics.num_del_files)
        if sync_statistics.num_del_dirs:
            self.log('%d directories were purged.' % sync_statistics.num_del_dirs)
        if sync_statistics.num_new_dirs:
            self.log('%d directories were created.' % sync_statistics.num_new_dirs)
        if sync_statistics.num_content_updates:
            self.log('%d files were updated by content.' % sync_statistics.num_content_updates)

        # Failure stats
        self.log('')
        if sync_statistics.num_copy_fld:
            self.log('there were errors in copying %d files.'
                     % sync_statistics.num_copy_fld)
        if sync_statistics.num_updates_fld:
            self.log('there were errors in updating %d files.'
                     % sync_statistics.num_updates_fld)
        if sync_statistics.num_del_dir_fld:
            self.log('there were errors in purging %d directories.'
                     % sync_statistics.num_del_dir_fld)
        if sync_statistics.num_del_file_fld:
            self.log('there were errors in purging %d files.'
                     % sync_statistics.num_del_file_fld)

    @staticmethod
    def _scan_dir(folder: str, sync_statistics: SyncStatistics = None) -> tuple:
        dir_items = set()
        file_items = set()
        for cwd, dirs, files in os.walk(folder):
            if sync_statistics:
                sync_statistics.num_dirs += len(dirs)

            for f in dirs:
                path = os.path.relpath(os.path.join(cwd, f), folder)
                dir_items.add(path)
            for f in files:
                path = os.path.relpath(os.path.join(cwd, f), folder)
                file_items.add(path)
        items = (dir_items, file_items)
        return items
