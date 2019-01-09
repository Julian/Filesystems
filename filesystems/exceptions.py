import errno
import os
import platform

import attr


class InvalidPath(Exception):
    """
    The given string path is not valid.
    """


class InvalidMode(Exception):
    """
    The given mode is not valid.
    """


@attr.s(hash=True)
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


class IsADirectory(_FileSystemError):
    errno = errno.EISDIR
    message = os.strerror(errno)


class DirectoryNotEmpty(_FileSystemError):
    errno = errno.ENOTEMPTY
    message = os.strerror(errno)


class NotADirectory(_FileSystemError):
    errno = errno.ENOTDIR
    message = os.strerror(errno)


class NotASymlink(_FileSystemError):
    errno = errno.EINVAL
    message = os.strerror(errno)


class PermissionError(_FileSystemError):
    errno = errno.EPERM
    message = os.strerror(errno)


class SymbolicLoop(_FileSystemError):
    errno = errno.ELOOP
    message = os.strerror(errno)


# On macOS, calling unlink on a directory raises EPERM.  I do not understand
# why, and man 2 unlink doesn't exactly discuss it, but it seems to be the
# case.
#
# On Linux you get the expected EISDIR.
if platform.system() == "Darwin":
    _UnlinkNonFileError = PermissionError
else:
    _UnlinkNonFileError = IsADirectory
