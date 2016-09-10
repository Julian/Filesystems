from unittest import TestCase

from testscenarios import with_scenarios

from filesystems import common
import filesystems.memory
import filesystems.native


FILESYSTEMS = [
    (name, dict(fs=getattr(filesystems, name).FS()))
    for name in "memory", "native"
]


@with_scenarios()
class TestChildren(TestCase):

    scenarios = FILESYSTEMS

    def test_it_returns_the_children(self):
        tempdir = self.fs.temporary_directory()
        self.addCleanup(self.fs.remove, tempdir)

        a = tempdir.descendant("a")
        b = tempdir.descendant("b")
        c = tempdir.descendant("b", "c")

        common.touch(fs=self.fs, path=a)
        self.fs.create_directory(path=b)
        common.touch(fs=self.fs, path=c)

        self.assertEqual(common.children(fs=self.fs, path=tempdir), {a, b})


@with_scenarios()
class TestTouch(TestCase):

    scenarios = FILESYSTEMS

    def test_it_creates_files(self):
        tempdir = self.fs.temporary_directory()
        self.addCleanup(self.fs.remove, tempdir)

        child = tempdir.descendant("a")
        self.assertFalse(self.fs.exists(path=child))

        common.touch(path=child, fs=self.fs)
        self.assertTrue(self.fs.exists(path=child))
