# -*- coding: utf-8 -*-
import errno
import os

from pyrsistent import s
from testscenarios import with_scenarios

from filesystems import Path, exceptions
from filesystems.common import _PY3
from filesystems._path import RelativePath


class TestFS(object):
    def test_open_read_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.open(tempdir.descendant("unittesting"))

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.ENOENT) +
                ": " +
                str(tempdir.descendant("unittesting"))
            ),
        )

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

    def test_open_append_binary_and_native_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), "ab") as f:
            f.write(b"some ")

        with fs.open(tempdir.descendant("unittesting"), "a") as f:
            f.write("things!")

        with fs.open(tempdir.descendant("unittesting")) as g:
            self.assertEqual(g.read(), "some things!")

    def test_open_append_native_and_binary_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), "a") as f:
            f.write("some ")

        with fs.open(tempdir.descendant("unittesting"), "ab") as f:
            f.write(b"things!")

        with fs.open(tempdir.descendant("unittesting")) as g:
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

        with fs.create(tempdir.descendant("unittesting")) as f:
            f.write(b"some things!")

        with fs.open(tempdir.descendant("unittesting")) as g:
            self.assertEqual(g.read(), "some things!")

    def test_create_file_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.create(tempdir.descendant("unittesting")):
            pass

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create(tempdir.descendant("unittesting"))

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.EEXIST) +
                ": " +
                str(tempdir.descendant("unittesting"))
            ),
        )

    def test_create_file_existing_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        fs.create_directory(tempdir.descendant("unittesting"))

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create(tempdir.descendant("unittesting"))

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.EEXIST) +
                ": " +
                str(tempdir.descendant("unittesting"))
            ),
        )

    def test_create_file_existing_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.link(source=source, to=to)

        with self.assertRaises(exceptions.FileExists) as e:
            fs.create(to)

        self.assertEqual(
            str(e.exception), os.strerror(errno.EEXIST) + ": " + str(to),
        )

    def test_create_non_existing_nested_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.create(tempdir.descendant("unittesting", "file"))

        self.assertEqual(
            str(e.exception), (
                os.strerror(errno.ENOENT) +
                ": " +
                str(tempdir.descendant("unittesting", "file"))
            )
        )

    def test_remove(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("directory")
        fs.create_directory(directory)

        a = directory.descendant("a")
        b = directory.descendant("b")
        c = directory.descendant("b", "c")
        d = directory.descendant("d")

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)
        fs.touch(path=d)

        fs.remove(directory)

        self.assertEqual(fs.children(path=tempdir), s())

    def test_remove_non_existing_thing(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("child")

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.remove(path=child)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(child),
        )

    def test_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        zero, one = tempdir.descendant("0"), tempdir.descendant("1")
        fs.create_directory(path=zero)
        fs.link(source=zero, to=one)

        fs.create_directory(path=zero.descendant("2"))
        three = one.descendant("3")
        fs.link(source=one.descendant("2"), to=three)

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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
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

        source = tempdir.descendant("source")
        first = tempdir.descendant("first")
        second = tempdir.descendant("second")
        third = tempdir.descendant("third")

        fs.link(source=source, to=first)
        fs.link(source=first, to=second)
        fs.link(source=second, to=third)

        with fs.open(source, "wb") as f:
            f.write(b"some things way over here!")

        self.assertEqual(fs.contents_of(third), "some things way over here!")

    def test_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.create_directory(source)
        fs.link(source=source, to=to)

        self.assertEqual(
            fs.realpath(to.descendant("child")),
            source.descendant("child"),
        )

    def test_link_descendant_of_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir.descendant("source")
        not_a_dir = tempdir.descendant("dir")
        fs.touch(not_a_dir)
        with self.assertRaises(exceptions.NotADirectory) as e:
            fs.link(source=source, to=not_a_dir.descendant("to"))

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTDIR) + ": " + str(not_a_dir),
        )

    def test_circular_links(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        stuck = tempdir.descendant("stuck")
        on = tempdir.descendant("on")
        loop = tempdir.descendant("loop")

        fs.link(source=stuck, to=on)
        fs.link(source=on, to=loop)
        fs.link(source=loop, to=stuck)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.realpath(stuck)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ELOOP) + ": " + str(stuck),
        )

    def test_direct_circular_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        loop = tempdir.descendant("loop")
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.realpath(loop)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ELOOP) + ": " + str(loop),
        )

    def test_link_into_a_circle(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        dont = tempdir.descendant("dont")
        fall = tempdir.descendant("fall")
        into = tempdir.descendant("into")
        the = tempdir.descendant("the")
        hole = tempdir.descendant("hole")

        fs.link(source=fall, to=dont)
        fs.link(source=into, to=fall)
        fs.link(source=the, to=into)
        fs.link(source=the, to=hole)
        fs.link(source=hole, to=the)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.realpath(dont)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ELOOP) + ": " + str(the),
        )

    def test_circular_loop_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        loop = tempdir.descendant("loop")
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.realpath(loop.descendant("child"))

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ELOOP) + ": " + str(loop),
        )

    def test_read_from_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.link(source=source, to=to)

        with fs.open(source, "wb") as f:
            f.write(b"some things over here!")

        self.assertEqual(fs.contents_of(to), "some things over here!")

    def test_write_to_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.link(source=source, to=to)

        with fs.open(to, "wb") as f:
            f.write(b"some things over here!")

        self.assertEqual(fs.contents_of(source), "some things over here!")

    def test_write_to_created_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.create_directory(source)
        fs.link(source=source, to=to)

        child = to.descendant("child")
        with fs.create(child) as f:
            f.write(b"some things over here!")

        self.assertEqual(fs.contents_of(child), "some things over here!")

    def test_read_from_loop(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir.descendant("loop")
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.open(path=loop)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ELOOP) + ": " + str(loop),
        )

    def test_write_to_loop(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir.descendant("loop")
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.open(path=loop, mode="wb")

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ELOOP) + ": " + str(loop),
        )

    def test_create_loop_descendant(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        loop = tempdir.descendant("loop")
        fs.link(source=loop, to=loop)

        with self.assertRaises(exceptions.SymbolicLoop) as e:
            fs.create(path=loop.descendant("child", "path"))

        # We'd really like the first one, but on a real native FS, looking for
        # it would be a race condition, so we allow the latter.
        acceptable = {
            os.strerror(errno.ELOOP) + ": " + str(loop),
            os.strerror(errno.ELOOP) + ": " + str(loop.descendant("child")),
        }

        self.assertIn(str(e.exception), acceptable)

    def test_link_nonexistant_parent(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir.descendant("source")
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.link(source=source, to=to)

        self.assertEqual(fs.realpath(to), source)

    def test_realpath_relative(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = RelativePath("source", "dir"), tempdir.descendant("to")
        fs.link(source=source, to=to)

        self.assertEqual(
            fs.realpath(to),
            to.sibling("source").descendant("dir"),
        )

    def test_realpath_normal_path(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source = tempdir.descendant("source")
        self.assertEqual(fs.realpath(source), source)

    def test_realpath_double_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        # /1 -> /0/1
        # /1/3 -> /1/2/3
        # realpath(/1/3) == /0/1/2/3

        zero, one = tempdir.descendant("0"), tempdir.descendant("1")
        two = one.descendant("2")
        fs.create_directory(path=zero)
        fs.create_directory(path=zero.descendant("1"))
        fs.link(source=zero.descendant("1"), to=one)
        fs.create_directory(path=two)
        fs.create_directory(path=two.descendant("3"))
        fs.link(source=two.descendant("3"), to=one.descendant("3"))

        self.assertEqual(
            fs.realpath(one.descendant("3")),
            zero.descendant("1", "2", "3"),
        )

    def test_remove_does_not_follow_directory_links(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("directory")
        fs.create_directory(path=directory)
        fs.touch(directory.descendant("a"))

        link = tempdir.descendant("link")
        fs.link(source=directory, to=link)
        self.assertTrue(fs.is_link(path=link))

        fs.remove(path=link)

        self.assertEqual(
            fs.children(path=directory), s(directory.descendant("a")),
        )

    def test_create_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("dir")
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

        directory = tempdir.descendant("dir")
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

        not_a_dir = tempdir.descendant("not_a_dir")
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

        link = tempdir.descendant("link")
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

        zero, one = tempdir.descendant("0"), tempdir.descendant("1")
        fs.create_directory(path=zero)
        fs.create_directory(path=zero.descendant("1"))
        fs.link(source=zero.descendant("1"), to=one)

        two = one.descendant("2")
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

        zero, one = tempdir.descendant("0"), tempdir.descendant("1")
        fs.create_directory(path=zero)
        fs.create_directory(path=zero.descendant("1"))
        fs.link(source=zero.descendant("1"), to=one)

        two = one.descendant("2")
        fs.create_directory(path=two)

        three, four = two.descendant("3"), two.descendant("4")
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

        directory = tempdir.descendant("dir")
        fs.create_directory(path=directory)
        self.assertTrue(fs.is_dir(path=directory))

        fs.remove_empty_directory(path=directory)
        self.assertFalse(fs.is_dir(path=directory))

    def test_remove_nonempty_empty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        nonempty = tempdir.descendant("dir")
        fs.create_directory(path=nonempty)
        fs.create_directory(nonempty.descendant("dir2"))
        self.assertTrue(fs.is_dir(path=nonempty))

        with self.assertRaises(exceptions.DirectoryNotEmpty) as e:
            fs.remove_empty_directory(path=nonempty)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOTEMPTY) + ": " + str(nonempty),
        )

    def test_remove_nonexisting_empty_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("dir")
        self.assertFalse(fs.is_dir(path=directory))

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.remove_empty_directory(path=directory)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(directory),
        )

    def test_remove_empty_directory_but_its_a_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("file")
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

        directory = tempdir.descendant("dir")
        fs.create_directory(path=directory)
        self.assertTrue(fs.is_dir(path=directory))

        link = tempdir.descendant("link")
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

        child = tempdir.descendant("child")
        fs.touch(path=child)
        self.assertTrue(fs.exists(path=child))

        fs.remove(path=child)
        self.assertFalse(fs.exists(path=child))

    def test_remove_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("child")
        fs.touch(path=child)
        self.assertTrue(fs.exists(path=child))

        fs.remove_file(path=child)
        self.assertFalse(fs.exists(path=child))

    def test_remove_nonexisting_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("child")
        self.assertFalse(fs.is_file(path=child))

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.remove_file(path=child)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(child),
        )

    def test_remove_file_on_a_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("child")
        fs.create_directory(path=child)
        self.assertTrue(fs.exists(path=child))

        fs.remove_file(path=child)
        self.assertFalse(fs.exists(path=child))

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

        nonexistant = tempdir.descendant("solipsism")
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

        a = tempdir.descendant("a")
        b = tempdir.descendant("b")
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

    def test_list_non_existing_directory(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("dir")
        self.assertFalse(fs.is_dir(path=directory))

        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.list_directory(directory)

        self.assertEqual(
            str(e.exception),
            os.strerror(errno.ENOENT) + ": " + str(directory),
        )

    def test_list_directory_link_child(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        # /1 -> /0/1
        # /1/3 -> /1/2/3
        # realpath(/1/3) == /0/1/2/3

        zero, one = tempdir.descendant("0"), tempdir.descendant("1")
        two = one.descendant("2")
        fs.create_directory(path=zero)
        fs.create_directory(path=zero.descendant("1"))
        fs.link(source=zero.descendant("1"), to=one)
        fs.create_directory(path=two)
        fs.create_directory(path=two.descendant("3"))
        self.assertEqual(set(fs.list_directory(two)), {"3"})

    def test_list_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        not_a_dir = tempdir.descendant("not_a_dir")
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

        child = tempdir.descendant("a")
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

        a = tempdir.descendant("a")
        b = tempdir.descendant("b")
        c = tempdir.descendant("b", "c")
        d = tempdir.descendant("d")

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)
        fs.link(source=c, to=d)

        self.assertEqual(fs.children(path=tempdir), s(a, b, d))

    def test_glob_children(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        a = tempdir.descendant("a")
        b = tempdir.descendant("b")
        c = tempdir.descendant("b", "c")
        abc = tempdir.descendant("abc")
        fedcba = tempdir.descendant("fedcba")

        fs.touch(path=a)
        fs.create_directory(path=b)
        fs.touch(path=c)
        fs.touch(path=abc)
        fs.touch(path=fedcba)

        self.assertEqual(
            fs.glob_children(path=tempdir, glob="*b*"),
            s(b, abc, fedcba),
        )

    def test_contents_of(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), "wb") as f:
            f.write(b"some more things!")

        self.assertEqual(
            fs.contents_of(tempdir.descendant("unittesting")),
            "some more things!",
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

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.link(source=source, to=to)
        self.assertEqual(fs.readlink(to), source)

    def test_readlink_nested_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir.descendant("source")
        first = tempdir.descendant("first")
        second = tempdir.descendant("second")
        third = tempdir.descendant("third")

        fs.link(source=source, to=first)
        fs.link(source=first, to=second)
        fs.link(source=second, to=third)
        self.assertEqual(fs.readlink(third), second)

    def test_readlink_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("child")
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

    def test_readlink_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        child = tempdir.descendant("child")
        with self.assertRaises(exceptions.FileNotFound) as e:
            fs.readlink(child)

        self.assertEqual(
            str(e.exception), os.strerror(errno.ENOENT) + ": " + str(child),
        )

    def test_readlink_relative(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)
        tempdir = fs.realpath(tempdir)

        source, to = RelativePath("source", "dir"), tempdir.descendant("to")
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

        zero, one = tempdir.descendant("0"), tempdir.descendant("1")
        two = one.descendant("2")
        fs.create_directory(path=zero)
        fs.create_directory(path=zero.descendant("1"))
        fs.link(source=zero.descendant("1"), to=one)
        fs.create_directory(path=two)
        fs.create_directory(path=two.descendant("3"))
        fs.link(source=two.descendant("3"), to=one.descendant("3"))

        self.assertEqual(
            fs.readlink(zero.descendant("1", "3")),
            two.descendant("3"),
        )


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
            with fs.open(tempdir.descendant("unittesting"), self.mode):
                pass


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

        with fs.open(tempdir.descendant("unittesting"), "wb") as f:
            f.write(self.bytes(self.expected))

        with fs.open(tempdir.descendant("unittesting"), self.mode) as g:
            contents = g.read()
            self.assertEqual(contents, self.expected)
            self.assertIsInstance(contents, type(self.expected))


@with_scenarios()
class OpenWriteNonExistingFileMixin(object):

    scenarios = [
        ("bytes", dict(contents=b"שלום", mode="wb")),
        ("native", dict(contents="שלום", mode="w")),
        ("text", dict(contents=u"שלום", mode="wt")),
    ]

    def test_open_write_non_existing_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), self.mode) as f:
            f.write(self.contents)

        with fs.open(tempdir.descendant("unittesting")) as g:
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

        with fs.open(tempdir.descendant("unittesting"), self.mode) as f:
            f.write(self.first)

        with fs.open(tempdir.descendant("unittesting"), self.mode) as f:
            f.write(self.second)

        with fs.open(tempdir.descendant("unittesting")) as g:
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

        with fs.open(tempdir.descendant("unittesting"), self.mode) as f:
            f.writelines(line + newline for line in to_write.splitlines())

        with fs.open(tempdir.descendant("unittesting")) as g:
            self.assertEqual(g.read(), text)
