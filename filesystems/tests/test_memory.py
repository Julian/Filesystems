from unittest import TestCase

from filesystems import memory
from filesystems.tests.common import TestFS


class TestMemory(TestFS, TestCase):
    FS = memory.FS

    def test_children_of_root(self):
        fs = self.FS()
        self.assertFalse(fs.children(Path.root()))

    def test_children_of_nonempty_root(self):
        fs = self.FS()
        fs.touch(Path("file"))
        self.assertEqual(set(fs.children(Path.root())), {Path("file")})
