from unittest import TestCase

from filesystems import native
from filesystems.tests.common import (
    InvalidModeMixin,
    NonExistentChildMixin,
    OpenAppendNonExistingFileMixin,
    OpenFileMixin,
    OpenWriteNonExistingFileMixin,
    SymbolicLoopMixin,
    TestFS,
    WriteLinesMixin,
)


class TestNative(TestFS, TestCase):
    FS = native.FS


class TestNativeInvalidMode(InvalidModeMixin, TestCase):
    FS = native.FS


class TestNativeOpenFile(OpenFileMixin, TestCase):
    FS = native.FS


class TestNativeOpenWriteNonExistingFile(
    OpenWriteNonExistingFileMixin,
    TestCase,
):
    FS = native.FS


class TestNativeOpenAppendNonExistingFile(
    OpenAppendNonExistingFileMixin,
    TestCase,
):
    FS = native.FS


class TestNativeWriteLines(WriteLinesMixin, TestCase):
    FS = native.FS


class TestNonExistentChild(NonExistentChildMixin, TestCase):
    FS = native.FS


class TestSymbolicLoops(SymbolicLoopMixin, TestCase):
    FS = native.FS
