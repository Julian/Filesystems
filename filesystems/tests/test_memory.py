from unittest import TestCase

from filesystems import Path, memory


class TestMemory(TestCase):
    def test_it_opens_files(self):
        fs = memory.FS()

        tempdir = fs.temporary_directory()
        self.addCleanup(fs.remove, tempdir)

        with fs.open(tempdir.descendant("unittesting"), "wb") as f:
            f.write("some things!")

        with fs.open(tempdir.descendant("unittesting")) as g:
            self.assertEqual(g.read(), "some things!")

    def test_create_directory(self):
        fs = memory.FS()

        directory = Path("dir")
        self.assertFalse(fs.is_dir(path=directory))

        fs.create_directory(path=directory)
        self.assertTrue(fs.is_dir(path=directory))

    def test_directory(self):
        fs = memory.FS()

        directory = Path("dir")
        fs.create_directory(directory)

        self.assertEqual(
            dict(
                exists=fs.exists(path=directory),
                is_dir=fs.is_dir(path=directory),
                is_file=fs.is_file(path=directory),
                is_link=fs.is_link(path=directory),
            ),
            dict(exists=True, is_dir=True, is_file=False, is_link=False),
        )

    def test_nonexistant(self):
        fs = memory.FS()

        nonexistant = Path.from_string(__file__).descendant("asdf")
        self.assertEqual(
            dict(
                exists=fs.exists(path=nonexistant),
                is_dir=fs.is_dir(path=nonexistant),
                is_file=fs.is_file(path=nonexistant),
                is_link=fs.is_link(path=nonexistant),
            ),
            dict(exists=False, is_dir=False, is_file=False, is_link=False),
        )
