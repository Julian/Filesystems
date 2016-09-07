class FS(object):
    """
    The native local filesystem.

    """

    def open(self, path):
        return open(str(path))
