from unittest import TestCase

from filesystems import native
from filesystems.tests.common import (
    TestFS,
    InvalidModeMixin,
    OpenFileMixin,
    OpenAppendNonExistingFileMixin,
    WriteLinesMixin,
)


class TestNative(TestFS, TestCase):
    FS = native.FS


class TestNativeInvalidMode(InvalidModeMixin, TestCase):
    FS = native.FS


class TestNativeOpenFile(OpenFileMixin, TestCase):
    FS = native.FS




class TestNativeOpenAppendNonExistingFile(
    OpenAppendNonExistingFileMixin,
    TestCase,
):
    FS = native.FS


class TestNativeWriteLines(WriteLinesMixin, TestCase):
    FS = native.FS
