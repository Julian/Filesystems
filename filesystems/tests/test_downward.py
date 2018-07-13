from unittest import TestCase

from filesystems import Path, downward, memory
from filesystems.tests.common import TestFS


class TestDownwardIsANormalFS(TestFS, TestCase):
    def FS(self):
        return downward.FS(on=memory.FS(), path=Path("subdir"))


class TestDownward(TestCase):
    def test_exists(self):
        parent = memory.FS()
        path = Path("subdir")
        parent.create_directory(path)
        parent.touch(path.descendant("file"))
        self.assertTrue(parent.exists(path=Path("subdir", "file")))

        fs = downward.FS(on=parent, path=path)

        self.assertTrue(fs.exists(path=Path("file")))

    def test_path_does_not_exist(self):
        pass
