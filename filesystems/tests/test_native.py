from unittest import TestCase

from testscenarios import TestWithScenarios

from filesystems import native
from filesystems.tests.common import (
    TestFS,
    TestInvalidMode,
    TestOpenFile,
    TestOpenAppendNonExistingFile,
    TestWriteLines,
)


class TestNative(TestFS, TestCase):
    FS = native.FS


class TestNativeInvalidMode(TestWithScenarios, TestInvalidMode, TestCase):
    FS = native.FS


class TestNativeOpenFile(TestWithScenarios, TestOpenFile, TestCase):
    FS = native.FS


class TestNativeOpenAppendNonExistingFile(
    TestWithScenarios,
    TestOpenAppendNonExistingFile,
    TestCase,
):
    FS = native.FS


class TestNativeWriteLines(TestWithScenarios, TestWriteLines, TestCase):
    FS = native.FS
