from unittest import TestCase, skipIf
import os

from zope.interface import verify

from filesystems import _PY36, exceptions, interfaces
from filesystems._path import Path, RelativePath


class TestPath(TestCase):
    def test_div(self):
        self.assertEqual(Path("a") / "b" / "c", Path("a", "b", "c"))

    def test_div_nonsense(self):
        with self.assertRaises(TypeError):
            Path("a") / object()

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

    def test_from_string_trailing_slash(self):
        self.assertEqual(
            Path.from_string(os.sep + os.sep.join("ab") + os.sep),
            Path("a", "b"),
        )

    # Not sure this is better than only stripping one, but it's easier to
    # do, so we start with this.
    def test_from_string_multiple_trailing_slashes(self):
        self.assertEqual(
            Path.from_string(os.sep + os.sep.join("ab") + os.sep + os.sep),
            Path("a", "b"),
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
                    "c"
                ),
            ),
            Path("", "", "a", "", "b", "c"),
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

    def test_repr(self):
        self.assertEqual(
            repr(Path("a", "b", "c")),
            "<Path /a/b/c>"
        )

    def test_expanded(self):
        self.assertEqual(
            Path.expanded("~/foo/~/bar"),
            Path.from_string(os.path.expanduser("~/foo/~/bar")),
        )

    def test_interface(self):
        verify.verifyClass(interfaces.Path, Path)

    @skipIf(not _PY36, "PathLike is PY3.6+")
    def test_is_pathlike(self):
        self.assertEqual(
            os.fspath(Path.from_string(os.sep + os.sep.join("abc"))),
            os.sep + os.sep.join("abc"),
        )


class TestRelativePath(TestCase):
    def test_div(self):
        self.assertEqual(
            RelativePath("a") / "b" / "c",
            RelativePath("a", "b", "c"),
        )

    def test_div_nonsense(self):
        with self.assertRaises(TypeError):
            RelativePath("a") / object()

    def test_relative_to(self):
        self.assertEqual(
            RelativePath("a", "b", "c").relative_to(Path("d", "e")),
            Path("d", "e", "a", "b", "c"),
        )

    def test_str(self):
        self.assertEqual(
            str(RelativePath("a", "b", "c")), os.path.join("a", "b", "c"),
        )

    def test_repr(self):
        self.assertEqual(
            repr(RelativePath("a", "b", "c")),
            "<Path a/b/c>"
        )

    def test_basename(self):
        self.assertEqual(RelativePath("a", "b").basename(), "b")

    def test_dirname(self):
        self.assertEqual(
            RelativePath("a", "b", "c").dirname(),
            os.path.join("a", "b"),
        )

    def test_parent(self):
        self.assertEqual(RelativePath("a", "b").parent(), RelativePath("a"))

    def test_heritage(self):
        self.assertEqual(
            list(RelativePath("a", "b", "c", "d").heritage()), [
                RelativePath("a"),
                RelativePath("a", "b"),
                RelativePath("a", "b", "c"),
                RelativePath("a", "b", "c", "d"),
            ],
        )

    def test_sibling(self):
        self.assertEqual(
            RelativePath("a", "b").sibling("c"),
            RelativePath("a", "c"),
        )

    def test_descendant(self):
        self.assertEqual(
            RelativePath("a", "b").descendant("c"),
            RelativePath("a", "b", "c"),
        )

    def test_multi_descendant(self):
        self.assertEqual(
            RelativePath("a").descendant("b", "c"),
            RelativePath("a", "b", "c"),
        )

    @skipIf(not _PY36, "PathLike is PY3.6+")
    def test_is_pathlike(self):
        self.assertEqual(
            os.fspath(RelativePath("a", "b", "c")),
            os.path.join("a", "b", "c"),
        )

    def test_interface(self):
        verify.verifyClass(interfaces.Path, RelativePath)
