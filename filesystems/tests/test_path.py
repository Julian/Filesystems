from unittest import TestCase
import os

from filesystems import Path, exceptions
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
        self.assertEqual(
            Path.from_string(os.sep + os.sep.join("abc")),
            Path("a", "b", "c"),
        )

    def test_from_string_relative(self):
        self.assertEqual(
            Path.from_string(os.sep.join("abc")),
            RelativePath("a", "b", "c"),
        )

    def test_from_string_repeated_separator(self):
        self.assertEqual(
            Path.from_string(
                (
                    os.sep * 3 +
                    "a" +
                    os.sep * 2 +
                    "b" +
                    os.sep +
                    "c" +
                    os.sep * 2
                ),
            ),
            Path("", "", "a", "", "b", "c", "", ""),
        )

    def test_from_string_relative_repeated_separator(self):
        self.assertEqual(
            Path.from_string("a" + os.sep * 3 + "b" + os.sep * 2 + "c"),
            RelativePath("a", "", "", "b",  "", "c"),
        )

    def test_from_string_parent(self):
        self.assertEqual(
            Path.from_string(
                (
                    os.pardir +
                    os.sep +
                    "a" +
                    os.sep +
                    "b" +
                    os.sep +
                    os.pardir +
                    os.sep +
                    "b"
                ),
            ),
            RelativePath(os.pardir, "a", "b", os.pardir, "b"),
        )

    def test_from_empty_string(self):
        with self.assertRaises(exceptions.InvalidPath):
            Path.from_string("")

    def test_str(self):
        self.assertEqual(
            str(Path.from_string(os.sep + os.sep.join("abc"))),
            os.sep + os.sep.join("abc"),
        )

    def test_cwd(self):
        self.assertEqual(Path.cwd(), Path.from_string(os.getcwd()))

    def test_cwd_is_absolute(self):
        self.assertEqual(Path.cwd().relative_to(Path.root()), Path.cwd())

    def test_root(self):
        self.assertEqual(Path.root(), Path())

    def test_root_heritage(self):
        self.assertEqual(list(Path.root().heritage()), [Path.root()])

    def test_basename(self):
        self.assertEqual(Path("a", "b").basename(), "b")

    def test_root_basename(self):
        self.assertEqual(Path().basename(), "")

    def test_dirname(self):
        self.assertEqual(
            Path("a", "b", "c").dirname(),
            os.path.join(os.sep, "a", "b"),
        )

    def test_root_dirname(self):
        self.assertEqual(Path().dirname(), os.sep)


class TestRelativePath(TestCase):
    def test_relative_to(self):
        self.assertEqual(
            RelativePath("a", "b", "c").relative_to(Path("d", "e")),
            Path("d", "e", "a", "b", "c"),
        )

    def test_str(self):
        self.assertEqual(
            str(RelativePath("a", "b", "c")), os.path.join("a", "b", "c"),
        )
