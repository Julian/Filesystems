# -*- coding: utf-8 -*-
import errno
import os

from pyrsistent import s
from testscenarios import multiply_scenarios, with_scenarios

from filesystems import Path, exceptions
from filesystems.common import _PY3
from filesystems._path import RelativePath


@with_scenarios()
class _NonExistingFileMixin(object):

    scenarios = [
        (
            "read_bytes",
            dict(act_on=lambda fs, path: fs.open(path=path, mode="rb")),
        ), (
            "read_native",
            dict(act_on=lambda fs, path: fs.open(path=path, mode="r")),
        ), (
            "read_text",
            dict(act_on=lambda fs, path: fs.open(path=path, mode="rt")),
        ), (
            "stat",
            dict(act_on=lambda fs, path: fs.stat(path=path)),
        ), (
            "lstat",
            dict(act_on=lambda fs, path: fs.lstat(path=path)),
        ), (
            "list_directory",
            dict(act_on=lambda fs, path: fs.list_directory(path=path)),
        ), (
            "remove_empty_directory",
            dict(act_on=lambda fs, path: fs.remove_empty_directory(path=path)),
        ), (
            "remove_file",
            dict(act_on=lambda fs, path: fs.remove_file(path=path)),
        ), (
            "readlink",
            dict(act_on=lambda fs, path: fs.readlink(path=path)),
        ),
    ]

    def test_non_existing(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.FileNotFound) as e:
            self.act_on(fs=fs, path=tempdir / "does not exist")

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(tempdir / "does not exist"),
        )


class TestFS(_NonExistingFileMixin):
    def test_open_read_non_existing_nested_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.open(tempdir.descendant("unittesting", "file"))

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.ENOENT) +
                ": " +
                str(tempdir.descendant("unittesting", "file"))
            )
        )

    def test_open_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.IsADirectory) as e:
            fs.open(tempdir)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EISDIR) + ": " + str(tempdir),
        )

    def test_open_append_binary_and_native_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", "ab") as f:
            f.write(b"some ")

        with fs.open(tempdir / "unittesting", "a") as f:
            f.write("things!")

        with fs.open(tempdir / "unittesting") as g:
            self.assertEqual(g.read(), "some things!")

    def test_open_append_native_and_binary_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", "a") as f:
            f.write("some ")

        with fs.open(tempdir / "unittesting", "ab") as f:
            f.write(b"things!")

        with fs.open(tempdir / "unittesting") as g:
            self.assertEqual(g.read(), "some things!")

    def test_open_append_non_existing_nested_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.open(tempdir.descendant("unittesting", "file"), "ab")

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.ENOENT) +
                ": " +
                str(tempdir.descendant("unittesting", "file"))
            )
        )

    def test_create_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.create(tempdir / "unittesting") as f:
            f.write("some things!")

        with fs.open(tempdir / "unittesting") as g:
            self.assertEqual(g.read(), "some things!")

    def test_create_file_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.create(tempdir / "unittesting"):
            pass

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create(tempdir / "unittesting")

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.EEXIST) +
                ": " +
                str(tempdir / "unittesting")
            ),
        )

    def test_create_file_existing_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.create_directory(tempdir / "unittesting")

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create(tempdir / "unittesting")

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.EEXIST) +
                ": " +
                str(tempdir / "unittesting")
            ),
        )

    def test_create_file_existing_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create(to)

        self.assertEqual(
            str(e.exception), os.strerror(errno.EEXIST) + ": " + str(to),
        )

    def test_get_contents(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", "wb") as f:
            f.write(b"some more things!")

        self.assertEqual(
            fs.get_contents(tempdir / "unittesting"),
            "some more things!",
        )

    def test_get_set_contents(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.set_contents(tempdir / "unittesting", "foo\nbar\nbaz")
        self.assertEqual(
            fs.get_contents(path=tempdir / "unittesting"),
            "foo\nbar\nbaz",
        )

    def test_get_contents_text(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", "wb") as f:
            f.write(b"שלום")

        self.assertEqual(
            fs.get_contents(tempdir / "unittesting", mode="t"),
            u"שלום",
        )

    def test_get_set_contents_text(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.set_contents(tempdir / "unittesting", u"שלום", mode="t")
        self.assertEqual(
            fs.get_contents(path=tempdir / "unittesting", mode="t"),
            u"שלום",
        )

    def test_set_contents_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.set_contents(tempdir / "unittesting", "foo\nbar\nbaz")
        fs.set_contents(tempdir / "unittesting", "spam\nquux\n")

        self.assertEqual(
            fs.get_contents(path=tempdir / "unittesting"),
            "spam\nquux\n",
        )

    def test_create_with_contents(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.create_with_contents(tempdir / "unittesting", "foo\nbar\nbaz")

        self.assertEqual(
            fs.get_contents(path=tempdir / "unittesting"),
            "foo\nbar\nbaz",
        )

    def test_create_with_contents_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.set_contents(tempdir / "unittesting", "foo\nbar\nbaz")
        with self.assertRaises(exceptions.FileExists):
            fs.create_with_contents(tempdir / "unittesting", "spam\nquux\n")

        self.assertEqual(
            fs.get_contents(path=tempdir / "unittesting"),
            "foo\nbar\nbaz",
        )

    def test_remove(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir / "directory"
        fs.create_directory(directory)

        a = directory / "a"
        b = directory / "b"
        c = directory.descendant("b", "c")
        d = directory / "d"

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)
        fs.touch(path=d)

        fs.remove(directory)

        self.assertEqual(fs.children(path=tempdir), s())

    def test_removing(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.removing(path=tempdir / "directory") as path:
            self.assertFalse(fs.is_dir(path=path))
            fs.create_directory(path=path)
            self.assertTrue(fs.is_dir(path=path))
        self.assertFalse(fs.is_dir(path=path))

    def test_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.touch(source)
        fs.link(source=source, to=to)

        self.assertEqual(
            dict(
                exists=fs.exists(path=to),
                is_dir=fs.is_dir(path=to),
                is_file=fs.is_file(path=to),
                is_link=fs.is_link(path=to),
            ), dict(
                exists=True,
                is_dir=False,
                is_file=True,
                is_link=True,
            ),
        )

    def test_link_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.create_directory(source)
        fs.link(source=source, to=to)

        self.assertEqual(
            dict(
                exists=fs.exists(path=to),
                is_dir=fs.is_dir(path=to),
                is_file=fs.is_file(path=to),
                is_link=fs.is_link(path=to),
            ), dict(
                exists=True,
                is_dir=True,
                is_file=False,
                is_link=True,
            ),
        )

    def test_link_directory_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        zero, one = tempdir / "0", tempdir / "1"
        fs.create_directory(path=zero)
        fs.link(source=zero, to=one)

        fs.create_directory(path=zero / "2")
        three = one / "3"
        fs.link(source=one / "2", to=three)

        self.assertEqual(
            dict(
                exists=fs.exists(path=three),
                is_dir=fs.is_dir(path=three),
                is_file=fs.is_file(path=three),
                is_link=fs.is_link(path=three),
            ),
            dict(exists=True, is_dir=True, is_file=False, is_link=True),
        )

    def test_link_nonexisting_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        self.assertEqual(
            dict(
                exists=fs.exists(path=to),
                is_dir=fs.is_dir(path=to),
                is_file=fs.is_file(path=to),
                is_link=fs.is_link(path=to),
            ), dict(
                exists=False,
                is_dir=False,
                is_file=False,
                is_link=True,
            ),
        )

    def test_link_existing_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.link(source=source, to=to)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EEXIST) + ": " + str(to),
        )

    def test_link_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.touch(path=to)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.link(source=source, to=to)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EEXIST) + ": " + str(to),
        )

    def test_link_existing_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.create_directory(path=to)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.link(source=source, to=to)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EEXIST) + ": " + str(to),
        )

    def test_link_nonexistant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        self.assertEqual(
            dict(
                exists=fs.exists(path=to),
                is_dir=fs.is_dir(path=to),
                is_file=fs.is_file(path=to),
                is_link=fs.is_link(path=to),
            ), dict(
                exists=False,
                is_dir=False,
                is_file=False,
                is_link=True,
            ),
        )

    def test_multiple_links(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir / "source"
        first = tempdir / "first"
        second = tempdir / "second"
        third = tempdir / "third"

        fs.link(source=source, to=first)
        fs.link(source=first, to=second)
        fs.link(source=second, to=third)

        with fs.open(source, "wb") as f:
            f.write(b"some things way over here!")

        self.assertEqual(fs.get_contents(third), "some things way over here!")

    def test_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.create_directory(source)
        fs.link(source=source, to=to)

        self.assertEqual(
            fs.realpath(to / "child"),
            source / "child",
        )

    def test_link_descendant_of_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir / "source"
        not_a_dir = tempdir / "dir"
        fs.touch(not_a_dir)
        with self.assertRaises(exceptions.NotADirectory) as e:
            fs.link(source=source, to=not_a_dir / "to")

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTDIR) + ": " + str(not_a_dir),
        )

    def test_read_from_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        with fs.open(source, "wb") as f:
            f.write(b"some things over here!")

        self.assertEqual(fs.get_contents(to), "some things over here!")

    def test_write_to_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        with fs.open(to, "wb") as f:
            f.write(b"some things over here!")

        self.assertEqual(fs.get_contents(source), "some things over here!")

    def test_write_to_created_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.create_directory(source)
        fs.link(source=source, to=to)

        child = to / "child"
        with fs.create(child) as f:
            f.write("some things over here!")

        self.assertEqual(fs.get_contents(child), "some things over here!")

    def test_link_nonexistant_parent(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir / "source"
        orphan = tempdir.descendant("nonexistant", "orphan")

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.link(source=source, to=orphan)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(orphan.parent()),
        )

    def test_realpath(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)

        self.assertEqual(fs.realpath(to), source)

    def test_realpath_relative(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = RelativePath("source", "dir"), tempdir / "to"
        fs.link(source=source, to=to)

        self.assertEqual(
            fs.realpath(to),
            to.sibling("source") / "dir",
        )

    def test_realpath_normal_path(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source = tempdir / "source"
        self.assertEqual(fs.realpath(source), source)

    def test_realpath_double_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        # /1 -> /0/1
        # /1/3 -> /1/2/3
        # realpath(/1/3) == /0/1/2/3

        zero, one = tempdir / "0", tempdir / "1"
        two = one / "2"
        fs.create_directory(path=zero)
        fs.create_directory(path=zero / "1")
        fs.link(source=zero / "1", to=one)
        fs.create_directory(path=two)
        fs.create_directory(path=two / "3")
        fs.link(source=two / "3", to=one / "3")

        self.assertEqual(
            fs.realpath(one / "3"),
            zero.descendant("1", "2", "3"),
        )

    def test_realpath_mega_link(self):
        """
        Now with even more nested links!

        Make sure we don't just accidentally solve the double link case
        and not the more general one.
        """
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        # /1 -> /0/1
        # /2/3 -> /1/2/3
        # /3 -> /2/3
        # /3/5 -> /3/4/5
        # realpath(/3/5) == /0/1/2/3/4/5

        directories = (
            tempdir / "0",
            tempdir / "1",
            tempdir / "2",
            tempdir / "3",
        )
        fs.create_directory(path=directories[0])
        fs.create_directory(path=directories[0] / "1")
        fs.create_directory(path=directories[2])
        fs.link(source=directories[0] / "1", to=directories[1])
        fs.create_directory(path=directories[1] / "2")
        fs.create_directory(path=directories[1] / "2" / "3")
        fs.link(source=directories[1] / "2" / "3", to=directories[2] / "3")
        fs.link(source=directories[2] / "3", to=directories[3])
        fs.link(source=directories[3] / "4" / "5", to=directories[3] / "5")

        self.assertEqual(
            fs.realpath(tempdir / "3" / "5"),
            directories[0].descendant("1", "2", "3", "4", "5"),
        )

    def test_remove_does_not_follow_directory_links(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir / "directory"
        fs.create_directory(path=directory)
        fs.touch(directory / "a")

        link = tempdir / "link"
        fs.link(source=directory, to=link)
        self.assertTrue(fs.is_link(path=link))

        fs.remove(path=link)

        self.assertEqual(
            fs.children(path=directory), s(directory / "a"),
        )

    def test_create_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir / "dir"
        self.assertFalse(fs.is_dir(path=directory))

        fs.create_directory(path=directory)

        self.assertEqual(
            dict(
                exists=fs.exists(path=directory),
                is_dir=fs.is_dir(path=directory),
                is_file=fs.is_file(path=directory),
                is_link=fs.is_link(path=directory),
            ),
            dict(exists=True, is_dir=True, is_file=False, is_link=False),
        )

    def test_create_existing_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir / "dir"
        fs.create_directory(path=directory)
        self.assertTrue(fs.is_dir(path=directory))

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create_directory(path=directory)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EEXIST) + ": " + str(directory),
        )

    def test_create_existing_directory_from_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        not_a_dir = tempdir / "not_a_dir"
        fs.touch(not_a_dir)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create_directory(path=not_a_dir)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EEXIST) + ": " + str(not_a_dir),
        )

    def test_create_existing_directory_from_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        link = tempdir / "link"
        fs.link(source=tempdir, to=link)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create_directory(path=link)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.EEXIST) + ": " + str(link),
        )

    def test_create_directory_parent_does_not_exist(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("some", "child", "dir")
        self.assertFalse(fs.is_dir(path=directory.parent()))

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.create_directory(path=directory)

        # Putting the first dir that doesn't exist would require some
        # traversal, so just stick with the parent for now.
        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(directory.parent()),
        )

    def test_create_directory_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        zero, one = tempdir / "0", tempdir / "1"
        fs.create_directory(path=zero)
        fs.create_directory(path=zero / "1")
        fs.link(source=zero / "1", to=one)

        two = one / "2"
        fs.create_directory(path=two)

        self.assertEqual(
            dict(
                exists=fs.exists(path=two),
                is_dir=fs.is_dir(path=two),
                is_file=fs.is_file(path=two),
                is_link=fs.is_link(path=two),
            ),
            dict(exists=True, is_dir=True, is_file=False, is_link=False),
        )

    def test_link_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        zero, one = tempdir / "0", tempdir / "1"
        fs.create_directory(path=zero)
        fs.create_directory(path=zero / "1")
        fs.link(source=zero / "1", to=one)

        two = one / "2"
        fs.create_directory(path=two)

        three, four = two / "3", two / "4"
        fs.touch(three)

        fs.link(source=three, to=four)

        self.assertEqual(
            dict(
                exists=fs.exists(path=four),
                is_dir=fs.is_dir(path=four),
                is_file=fs.is_file(path=four),
                is_link=fs.is_link(path=four),
            ),
            dict(exists=True, is_dir=False, is_file=True, is_link=True),
        )

    def test_remove_empty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir / "dir"
        fs.create_directory(path=directory)
        self.assertTrue(fs.is_dir(path=directory))

        fs.remove_empty_directory(path=directory)
        self.assertFalse(fs.is_dir(path=directory))

    def test_remove_nonempty_empty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        nonempty = tempdir / "dir"
        fs.create_directory(path=nonempty)
        fs.create_directory(nonempty / "dir2")
        self.assertTrue(fs.is_dir(path=nonempty))

        with self.assertRaises(exceptions.DirectoryNotEmpty) as e:
            fs.remove_empty_directory(path=nonempty)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTEMPTY) + ": " + str(nonempty),
        )

    def test_remove_empty_directory_but_its_a_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "file"
        fs.touch(path=child)
        self.assertTrue(fs.is_file(path=child))

        with self.assertRaises(exceptions.NotADirectory) as e:
            fs.remove_empty_directory(path=child)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTDIR) + ": " + str(child),
        )

    def test_remove_empty_directory_but_its_a_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir / "dir"
        fs.create_directory(path=directory)
        self.assertTrue(fs.is_dir(path=directory))

        link = tempdir / "link"
        fs.link(source=directory, to=link)
        self.assertTrue(fs.is_dir(path=link))

        with self.assertRaises(exceptions.NotADirectory) as e:
            fs.remove_empty_directory(path=link)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTDIR) + ": " + str(link),
        )

    def test_remove_on_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "child"
        fs.touch(path=child)
        self.assertTrue(fs.exists(path=child))

        fs.remove(path=child)
        self.assertFalse(fs.exists(path=child))

    def test_remove_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "child"
        fs.touch(path=child)
        self.assertTrue(fs.exists(path=child))

        fs.remove_file(path=child)
        self.assertFalse(fs.exists(path=child))

    def test_remove_file_on_empty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "child"
        fs.create_directory(path=child)
        self.assertTrue(fs.exists(path=child))

        with self.assertRaises(exceptions._UnlinkNonFileError) as e:
            fs.remove_file(path=child)
        self.assertEqual(
            str(e.exception), (
                os.strerror(exceptions._UnlinkNonFileError.errno) +
                ": " +
                str(child)
            ),
        )

    def test_remove_file_on_nonempty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "child"
        fs.create_directory(path=child)
        fs.touch(child / "grandchild")
        self.assertTrue(fs.exists(path=child))

        with self.assertRaises(exceptions._UnlinkNonFileError) as e:
            fs.remove_file(path=child)
        self.assertEqual(
            str(e.exception), (
                os.strerror(exceptions._UnlinkNonFileError.errno) +
                ": " +
                str(child)
            ),
        )

    def test_remove_nonexisting_file_nonexisting_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("dir", "child")
        self.assertFalse(fs.is_file(path=child))

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.remove_file(path=child)

        self.assertEqual(
            str(e.exception), os.strerror(errno.ENOENT) + ": " + str(child),
        )

    def test_non_existing_file_types(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        nonexistant = tempdir / "solipsism"
        self.assertEqual(
            dict(
                exists=fs.exists(path=nonexistant),
                is_dir=fs.is_dir(path=nonexistant),
                is_file=fs.is_file(path=nonexistant),
                is_link=fs.is_link(path=nonexistant),
            ),
            dict(exists=False, is_dir=False, is_file=False, is_link=False),
        )

    def test_list_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        a = tempdir / "a"
        b = tempdir / "b"
        c = tempdir.descendant("b", "c")

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)

        self.assertEqual(set(fs.list_directory(tempdir)), {"a", "b"})

    def test_list_empty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        self.assertEqual(set(fs.list_directory(tempdir)), set())

    def test_list_directory_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        # /source -> /link
        # /source/{1, 2, 3}

        source, link = tempdir / "source", tempdir / "link"

        fs.create_directory(path=source)
        fs.create_directory(path=source / "1")
        fs.touch(path=source / "2")
        fs.touch(path=source / "3")

        fs.link(source=source, to=link)

        self.assertEqual(set(fs.list_directory(link)), s("1", "2", "3"))

    def test_list_directory_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        # /1 -> /0/1
        # /1/3 -> /1/2/3
        # realpath(/1/3) == /0/1/2/3

        zero, one = tempdir / "0", tempdir / "1"
        two = one / "2"
        fs.create_directory(path=zero)
        fs.create_directory(path=zero / "1")
        fs.link(source=zero / "1", to=one)
        fs.create_directory(path=two)
        fs.create_directory(path=two / "3")
        self.assertEqual(set(fs.list_directory(two)), {"3"})

    def test_list_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        not_a_dir = tempdir / "not_a_dir"
        fs.touch(not_a_dir)

        with self.assertRaises(exceptions.NotADirectory) as e:
            fs.list_directory(not_a_dir)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTDIR) + ": " + str(not_a_dir),
        )

    def test_touch(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "a"
        self.assertFalse(fs.exists(path=child))

        fs.touch(path=child)
        self.assertEqual(
            dict(
                exists=fs.exists(path=child),
                is_dir=fs.is_dir(path=child),
                is_file=fs.is_file(path=child),
                is_link=fs.is_link(path=child),
            ),
            dict(exists=True, is_dir=False, is_file=True, is_link=False),
        )

    def test_children(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        a = tempdir / "a"
        b = tempdir / "b"
        c = tempdir.descendant("b", "c")
        d = tempdir / "d"

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)
        fs.link(source=c, to=d)

        self.assertEqual(fs.children(path=tempdir), s(a, b, d))

    def test_glob_children(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        a = tempdir / "a"
        b = tempdir / "b"
        c = tempdir.descendant("b", "c")
        abc = tempdir / "abc"
        fedcba = tempdir / "fedcba"

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)
        fs.touch(path=abc)
        fs.touch(path=fedcba)

        self.assertEqual(
            fs.glob_children(path=tempdir, glob="*b*"),
            s(b, abc, fedcba),
        )

    # With how crazy computers are, I'm not actually 100% sure that
    # these tests for the behavior of the root directory will always be
    # the case. But, onward we go.
    def test_root_always_exists(self):
        fs = self.FS()
        self.assertTrue(fs.exists(Path.root()))

    def test_realpath_root(self):
        fs = self.FS()
        self.assertEqual(fs.realpath(Path.root()), Path.root())

    def test_readlink_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir / "source", tempdir / "to"
        fs.link(source=source, to=to)
        self.assertEqual(fs.readlink(to), source)

    def test_readlink_nested_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir / "source"
        first = tempdir / "first"
        second = tempdir / "second"
        third = tempdir / "third"

        fs.link(source=source, to=first)
        fs.link(source=first, to=second)
        fs.link(source=second, to=third)
        self.assertEqual(fs.readlink(third), second)

    def test_readlink_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir / "child"
        fs.touch(child)
        with self.assertRaises(exceptions.NotASymlink) as e:
            fs.readlink(child)

        self.assertEqual(
            str(e.exception), os.strerror(errno.EINVAL) + ": " + str(child),
        )

    def test_readlink_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.NotASymlink) as e:
            fs.readlink(tempdir)

        self.assertEqual(
            str(e.exception), os.strerror(errno.EINVAL) + ": " + str(tempdir),
        )

    def test_readlink_relative(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = RelativePath("source", "dir"), tempdir / "to"
        fs.link(source=source, to=to)

        self.assertEqual(fs.readlink(to), source)

    def test_readlink_child_link_from_source(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        # /1 -> /0/1
        # /1/3 -> /1/2/3
        # readlink(/0/1/3) == /1/2/3

        zero, one = tempdir / "0", tempdir / "1"
        two = one / "2"
        fs.create_directory(path=zero)
        fs.create_directory(path=zero / "1")
        fs.link(source=zero / "1", to=one)
        fs.create_directory(path=two)
        fs.create_directory(path=two / "3")
        fs.link(source=two / "3", to=one / "3")

        self.assertEqual(fs.readlink(zero.descendant("1", "3")), two / "3")


@with_scenarios()
class InvalidModeMixin(object):

    scenarios = [
        ("activity", {"mode": "z"}),
        ("mode", {"mode": "rz"}),
        ("extra", {"mode": "rbz"}),
        ("binary_and_text", {"mode": "rbt"}),
        ("read_and_write", {"mode": "rwb"}),
    ]

    def test_invalid_mode(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.InvalidMode):
            fs.open(tempdir / "unittesting", self.mode)


@with_scenarios()
class OpenFileMixin(object):
    scenarios = [
        (
            "bytes",
            {
                "expected": b"some things!",
                "bytes": lambda c: c,
                "mode": "rb",
            },
        ),
        (
            "native",
            {
                "expected": "some things!",
                "bytes": lambda c: c.encode() if _PY3 else c,
                "mode": "r",
            },
        ),
        (
            "text",
            {
                "expected": u"some things!",
                "bytes": lambda c: c.encode(),
                "mode": "rt",
            },
        ),
    ]

    def test_open_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", "wb") as f:
            f.write(self.bytes(self.expected))

        with fs.open(tempdir / "unittesting", self.mode) as g:
            contents = g.read()
            self.assertEqual(contents, self.expected)
            self.assertIsInstance(contents, type(self.expected))


@with_scenarios()
class OpenWriteNonExistingFileMixin(object):

    scenarios = [
        ("bytes", dict(contents=u"שלום".encode("utf-8"), mode="wb")),
        ("native", dict(contents="שלום", mode="w")),
        ("text", dict(contents=u"שלום", mode="wt")),
    ]

    def test_open_write_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", self.mode) as f:
            f.write(self.contents)

        with fs.open(tempdir / "unittesting") as g:
            self.assertEqual(g.read(), "שלום")


@with_scenarios()
class OpenAppendNonExistingFileMixin(object):

    scenarios = [
        ("bytes", dict(first=b"some ", second=b"things!", mode="ab")),
        ("native", dict(first="some ", second="things!", mode="a")),
        ("text", dict(first=u"some ", second=u"things!", mode="at")),
    ]

    def test_open_append_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir / "unittesting", self.mode) as f:
            f.write(self.first)

        with fs.open(tempdir / "unittesting", self.mode) as f:
            f.write(self.second)

        with fs.open(tempdir / "unittesting") as g:
            self.assertEqual(g.read(), "some things!")


@with_scenarios()
class WriteLinesMixin(object):

    scenarios = [
        (
            "bytes",
            {
                "to_write": lambda text: text.encode(),
                "mode": "ab",
            },
        ),
        (
            "native",
            {
                "to_write": lambda text: text if _PY3 else text.encode(),
                "mode": "a",
            },
        ),
        (
            "text",
            {
                "to_write": lambda text: text,
                "mode": "at",
            },
        ),
    ]

    def test_writelines(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        text = u"some\nthings!\n"
        newline = self.to_write(u"\n")
        to_write = self.to_write(text)

        with fs.open(tempdir / "unittesting", self.mode) as f:
            f.writelines(line + newline for line in to_write.splitlines())

        with fs.open(tempdir / "unittesting") as g:
            self.assertEqual(g.read(), text)


@with_scenarios()
class NonExistentChildMixin(object):

    scenarios = multiply_scenarios(
        [
            (
                "directory", dict(
                    Exception=exceptions.FileNotFound,
                    create=lambda fs, path: fs.create_directory(path=path),
                ),
            ), (
                "file", dict(
                    Exception=exceptions.NotADirectory,
                    create=lambda fs, path: fs.touch(path=path),
                ),
            ), (
                "link_to_file", dict(
                    Exception=exceptions.FileNotFound,
                    create=lambda fs, path: fs.touch(  # Sorry :/
                        path=path.sibling("source"),
                    ) and fs.link(source=path.sibling("source"), to=path),
                ),
                "link_to_directory", dict(
                    Exception=exceptions.FileNotFound,
                    create=lambda fs, path: fs.create_directory(  # Sorry :/
                        path=path.sibling("source"),
                    ) and fs.link(source=path.sibling("source"), to=path),
                ),
                "loop", dict(
                    Exception=exceptions.SymbolicLoop,
                    create=lambda fs, path: fs.link(source=path, to=path),
                ),
            ),
        ], [
            (
                "create_directory", dict(
                    act_on=lambda fs, path: fs.create_directory(path=path),
                    error_on_child=False,
                ),
            ), (
                "list_directory",
                dict(act_on=lambda fs, path: fs.list_directory(path=path)),
            ), (
                "create_file",
                dict(act_on=lambda fs, path: fs.create(path=path)),
            ), (
                "remove_file",
                dict(act_on=lambda fs, path: fs.remove_file(path=path)),
            ), (
                "remove_empty_directory", dict(
                    act_on=lambda fs, path: fs.remove_empty_directory(
                        path=path,
                    ),
                ),
            ), (
                "read_bytes",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="rb")),
            ), (
                "read_native",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="r")),
            ), (
                "read_text",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="rt")),
            ), (
                "write_bytes",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="wb")),
            ), (
                "write_native",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="w")),
            ), (
                "write_text",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="wt")),
            ), (
                "append_bytes",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="ab")),
            ), (
                "append_native",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="a")),
            ), (
                "append_text",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="at")),
            ), (
                "link", dict(
                    act_on=lambda fs, path: fs.link(source=path, to=path),
                    error_on_child=False,
                ),
            ), (
                "readlink", dict(
                    act_on=lambda fs, path: fs.readlink(path=path),
                ),
            ), (
                "stat", dict(
                    act_on=lambda fs, path: fs.stat(path=path),
                ),
            ), (
                "lstat", dict(
                    act_on=lambda fs, path: fs.lstat(path=path),
                ),
            ),
        ],
    )

    def test_child_of_non_existing(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        existing = tempdir / "unittesting"
        self.create(fs=fs, path=existing)

        non_existing_child = existing.descendant("non_existing", "thing")
        with self.assertRaises(self.Exception) as e:
            self.act_on(fs=fs, path=non_existing_child)

        path = (  # Sorry :/
            non_existing_child
            if getattr(self, "error_on_child", True)
            else non_existing_child.parent()
        )

        self.assertEqual(
            str(e.exception),
            os.strerror(self.Exception.errno) + ": " + str(path),
        )

    def test_exists(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        existing = tempdir / "unittesting"
        self.create(fs=fs, path=existing)

        non_existing_child = existing.descendant("non_existing", "thing")
        self.assertFalse(fs.exists(non_existing_child))


@with_scenarios()
class _SymbolicLoopMixin(object):

    scenarios = multiply_scenarios(
        [  # Size of loop
            ("one", dict(chain=["loop"])),
            ("two", dict(chain=["one", "two"])),
            ("many", dict(chain=["don't", "fall", "in", "the", "hole"])),
        ],
        [  # Path to operate on
            ("itself", dict(path=lambda loop: loop)),
            ("child", dict(path=lambda loop: loop / "child")),
        ],
        [  # Operation
            (
                "realpath",
                dict(act_on=lambda fs, path: fs.realpath(path=path)),
            ), (
                "list_directory",
                dict(act_on=lambda fs, path: fs.list_directory(path=path)),
            ), (
                "read_bytes",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="rb")),
            ), (
                "read_native",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="r")),
            ), (
                "read_text",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="rt")),
            ), (
                "write_bytes",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="wb")),
            ), (
                "write_native",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="w")),
            ), (
                "write_text",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="wt")),
            ), (
                "append_bytes",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="ab")),
            ), (
                "append_native",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="a")),
            ), (
                "append_text",
                dict(act_on=lambda fs, path: fs.open(path=path, mode="at")),
            ), (
                "stat",
                dict(act_on=lambda fs, path: fs.stat(path=path)),
            ), (
                "exists",
                dict(act_on=lambda fs, path: fs.exists(path=path)),
            ), (
                "is_dir",
                dict(act_on=lambda fs, path: fs.is_dir(path=path)),
            ), (
                "is_file",
                dict(act_on=lambda fs, path: fs.is_file(path=path)),
            ),
        ],
    )

    def fs_with_loop(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        for source, to in zip(self.chain, self.chain[1:]):
            fs.link(source=tempdir / source, to=tempdir / to)
        fs.link(
            source=tempdir / self.chain[-1],
            to=tempdir / self.chain[0],
        )

        return fs, tempdir.descendant(self.chain[0])

    def test_it_detects_loops(self):
        fs, loop = self.fs_with_loop()
        with self.assertRaises(exceptions.SymbolicLoop):
            self.act_on(fs=fs, path=self.path(loop))

        # FIXME: Temporarily disabled, since this is "wrong" at the minute for
        #        memory.FS.
        # self.assertEqual(
        #     str(e.exception),
        #     os.strerror(errno.ELOOP) + ": " + str(self.path(loop)),
        # )


class SymbolicLoopMixin(_SymbolicLoopMixin):
    def test_create_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.create(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_create_directory_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.create_directory(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_remove_file_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.remove_file(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_remove_empty_directory_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.remove_empty_directory(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_link_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.link(source=tempdir, to=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_readlink_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.readlink(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
            os.strerror(errno.ELOOP) + ": " + str(
                loop.descendant("child", "path"),
            ),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_lstat_loop(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)
        self.assertTrue(fs.lstat(path=loop))

    def test_lstat_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.lstat(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
            os.strerror(errno.ELOOP) + ": " + str(
                loop.descendant("child", "path"),
            ),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_is_link_loop(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)
        self.assertTrue(fs.is_link(path=loop))

    def test_is_link_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir / "loop"
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.is_link(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop / "child"),
            os.strerror(errno.ELOOP) + ": " + str(
                loop.descendant("child", "path"),
            ),
        }

        self.assertIn(str(e.exception), acceptable)
