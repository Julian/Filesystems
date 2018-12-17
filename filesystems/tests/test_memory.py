from unittest import TestCase

from pyrsistent import s

from filesystems import Path, memory
from filesystems.tests.common import (
    TestFS,
    InvalidModeMixin,
    NonExistentChildMixin,
    OpenFileMixin,
    OpenAppendNonExistingFileMixin,
    OpenWriteNonExistingFileMixin,
    SymbolicLoopMixin,
    WriteLinesMixin,
)


class TestMemory(TestFS, TestCase):
    FS = staticmethod(memory.FS)

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


class TestMemoryInvalidMode(InvalidModeMixin, TestCase):
    FS = staticmethod(memory.FS)


class TestMemoryOpenFile(OpenFileMixin, TestCase):
    FS = staticmethod(memory.FS)


class TestMemoryOpenWriteNonExistingFile(
    OpenWriteNonExistingFileMixin,
    TestCase,
):
    FS = staticmethod(memory.FS)


class TestMemoryOpenAppendNonExistingFile(
    OpenAppendNonExistingFileMixin,
    TestCase,
):
    FS = staticmethod(memory.FS)


class TestMemoryWriteLines(WriteLinesMixin, TestCase):
    FS = staticmethod(memory.FS)


class TestNonExistentChild(NonExistentChildMixin, TestCase):
    FS = staticmethod(memory.FS)


class TestSymbolicLoops(SymbolicLoopMixin, TestCase):
    FS = staticmethod(memory.FS)
