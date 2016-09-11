import errno
import os

from characteristic import Attribute, attributes


@attributes([Attribute(name="value", exclude_from_init=True)])
class _FileSystemError(Exception):
    def __init__(self, value=None):
        super(_FileSystemError, self).__init__(value)
        self.value = value

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
