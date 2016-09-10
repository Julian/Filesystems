import os
import tempfile

from filesystems import Path
from filesystems.common import children


class FS(object):
    """
    The native local filesystem.

    """

    def open(self, path, mode="rb"):
        return open(str(path), mode)

    def remove(self, path):
        if self.is_dir(path=path) and not self.is_link(path=path):
            for child in children(fs=self, path=path):
                self.remove(path=child)
            os.rmdir(str(path))
        else:
            os.remove(str(path))

    def create_directory(self, path):
        os.mkdir(str(path))

    def listdir(self, path):
        return os.listdir(str(path))

    def temporary_directory(self):
        return Path.from_string(tempfile.mkdtemp())

    def exists(self, path):
        return os.path.exists(str(path))

    def is_dir(self, path):
        return os.path.isdir(str(path))

    def is_file(self, path):
        return os.path.isfile(str(path))

    def is_link(self, path):
        return os.path.islink(str(path))
