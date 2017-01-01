import errno
import os

import attr


@attr.s
class _FileSystemError(Exception):

    value = attr.ib(default=None)

    def __str__(self):
        if self.value is None:
            return self.message
        return "{self.message}: {self.value}".format(self=self)


class FileNotFound(_FileSystemError):
    errno = errno.ENOENT
    message = os.strerror(errno)


class FileExists(_FileSystemError):
    errno = errno.EEXIST
    message = os.strerror(errno)


class DirectoryNotEmpty(_FileSystemError):
    errno = errno.ENOTEMPTY
    message = os.strerror(errno)
