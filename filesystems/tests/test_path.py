from unittest import TestCase
import os

from filesystems import Path
from filesystems._path import RelativePath


class TestPath(TestCase):
    def test_descendant(self):
        self.assertEqual(Path("a", "b").descendant("c"), Path("a", "b", "c"))

    def test_multi_descendant(self):
        self.assertEqual(Path("a").descendant("b", "c"), Path("a", "b", "c"))

    def test_parent(self):
        self.assertEqual(Path("a", "b").parent(), Path("a"))

    def test_parent_of_root(self):
        self.assertEqual(Path.root().parent(), Path.root())

    def test_sibling(self):
        self.assertEqual(Path("a", "b").sibling("c"), Path("a", "c"))

    def test_sibling_of_root(self):
        with self.assertRaises(ValueError):
            Path.root().sibling("c")

    def test_relative_to(self):
        self.assertEqual(
            Path("a", "b", "c").relative_to(Path("d", "e")),
            Path("a", "b", "c"),
        )

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

    def test_str(self):
        self.assertEqual(str(Path.from_string("/a/b/c")), "/a/b/c")

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

    def test_dirname(self):
        self.assertEqual(Path("a", "b", "c").dirname(), "/a/b")

    def test_root_dirname(self):
        self.assertEqual(Path().dirname(), "/")


class TestRelativePath(TestCase):
    def test_relative_to(self):
        self.assertEqual(
            RelativePath("a", "b", "c").relative_to(Path("d", "e")),
            Path("d", "e", "a", "b", "c"),
        )

    def test_str(self):
        self.assertEqual(str(RelativePath("a", "b", "c")), "a/b/c")
