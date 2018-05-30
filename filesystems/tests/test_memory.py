from unittest import TestCase

from pyrsistent import s
from testscenarios import TestWithScenarios

from filesystems import Path, memory
from filesystems.tests.common import (
    TestFS,
    TestInvalidMode,
    TestOpenFile,
    TestOpenAppendNonExistingFile,
    TestWriteLines,
)


class TestMemory(TestFS, TestCase):
    FS = memory.FS

    def test_children_of_root(self):
        fs = self.FS()
        self.assertFalse(fs.children(Path.root()))

    def test_children_of_nonempty_root(self):
        fs = self.FS()
        fs.touch(Path("file"))
        self.assertEqual(fs.children(Path.root()), s(Path("file")))

    def test_instances_are_independent(self):
        fs = self.FS()
        fs.touch(Path("file"))
        self.assertTrue(fs.exists(Path("file")))
        self.assertFalse(self.FS().exists(Path("file")))


class TestMemoryInvalidMode(TestWithScenarios, TestInvalidMode, TestCase):
    FS = memory.FS


class TestMemoryOpenFile(TestWithScenarios, TestOpenFile, TestCase):
    FS = memory.FS


class TestMemoryOpenAppendNonExistingFile(
    TestWithScenarios,
    TestOpenAppendNonExistingFile,
    TestCase,
):
    FS = memory.FS


class TestMemoryWriteLines(TestWithScenarios, TestWriteLines, TestCase):
    FS = memory.FS
