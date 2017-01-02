from unittest import TestCase
import os

from filesystems import Path


class TestPath(TestCase):
    def test_descendant(self):
        self.assertEqual(Path("a", "b").descendant("c"), Path("a", "b", "c"))

    def test_multi_descendant(self):
        self.assertEqual(Path("a").descendant("b", "c"), Path("a", "b", "c"))

    def test_parent(self):
        self.assertEqual(Path("a", "b").parent(), Path("a"))

    def test_parent_of_root(self):
        self.assertEqual(Path.root().parent(), Path.root())

    def test_heritage(self):
        self.assertEqual(
            list(Path("a", "b", "c", "d").heritage()), [
                Path("a"),
                Path("a", "b"),
                Path("a", "b", "c"),
                Path("a", "b", "c", "d"),
            ],
        )

    def test_from_string(self):
        self.assertEqual(Path.from_string("/a/b/c"), Path("a", "b", "c"))

    def test_from_relative_string(self):
        self.assertEqual(
            Path.from_string("a/b/c"), Path.cwd().descendant("a", "b", "c"),
        )

    def test_cwd(self):
        self.assertEqual(Path.cwd(), Path.from_string(os.getcwd()))

    def test_root(self):
        self.assertEqual(Path.root(), Path())

    def test_root_heritage(self):
        self.assertEqual(list(Path.root().heritage()), [Path.root()])

    def test_basename(self):
        self.assertEqual(Path("a", "b").basename(), "b")

    def test_root_basename(self):
        self.assertEqual(Path().basename(), "")
