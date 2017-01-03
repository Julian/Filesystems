from unittest import skip
import errno
import os

from filesystems import Path, exceptions


class TestFS(object):
    def test_open_file(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), "wb") as f:
            f.write(b"some things!")

        with fs.open(tempdir.descendant("unittesting")) as g:
            self.assertEqual(g.read(), b"some things!")

    def test_open_non_existing_file(self):
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

    def test_open_non_existing_nested_file(self):
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

        self.assertEqual(fs.children(path=tempdir), set())

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

        self.assertEqual(fs.contents_of(third), b"some things way over here!")

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

    def test_realpath_normal_path(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source = tempdir.descendant("source")
        self.assertEqual(fs.realpath(source), source)

    def test_circular_links(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

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

        self.assertEqual(fs.contents_of(to), b"some things over here!")

    def test_write_to_link(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        source, to = tempdir.descendant("source"), tempdir.descendant("to")
        fs.link(source=source, to=to)

        with fs.open(to, "wb") as f:
            f.write(b"some things over here!")

        self.assertEqual(fs.contents_of(source), b"some things over here!")

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

    @skip("No symlink support yet.")
    def test_remove_does_not_follow_directory_links(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        directory = tempdir.descendant("directory")
        fs.create_directory(path=directory)
        fs.touch(directory.descendant("a"))

        link = tempdir.descendant("link")
        fs.symlink(source=directory, target=link)
        self.assertTrue(fs.is_link(path=link))

        fs.remove(path=link)

        self.assertEqual(
            fs.children(path=directory), {directory.descendant("a")},
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

        self.assertEqual(fs.children(path=tempdir), {a, b, d})

    def test_contents_of(self):
        fs = self.FS()
        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), "wb") as f:
            f.write(b"some more things!")

        self.assertEqual(
            fs.contents_of(tempdir.descendant("unittesting")),
            b"some more things!",
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
