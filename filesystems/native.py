import os


class FS(object):
    """
    The native local filesystem.

    """

    def open(self, path):
        return open(str(path))

    def exists(self, path):
        return os.path.exists(str(path))

    def is_dir(self, path):
        return os.path.isdir(str(path))

    def is_file(self, path):
        return os.path.isfile(str(path))

    def is_link(self, path):
        return os.path.islink(str(path))
