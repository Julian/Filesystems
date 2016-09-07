from unittest import TestCase

from filesystems import Path, native


class TestNative(TestCase):

    fs = native.FS()

    def test_it_opens_local_files(self):
        path = Path.from_string(__file__)
        with self.fs.open(path) as got, open(__file__) as expected:
            self.assertEqual(got.read(), expected.read())

    def test_directory(self):
        directory = Path.from_string(__file__).parent()
        self.assertEqual(
            dict(
                exists=self.fs.exists(path=directory),
                is_dir=self.fs.is_dir(path=directory),
                is_file=self.fs.is_file(path=directory),
                is_link=self.fs.is_link(path=directory),
            ),
            dict(exists=True, is_dir=True, is_file=False, is_link=False),
        )

    def test_nonexistant(self):
        nonexistant = Path.from_string(__file__).descendant("asdf")
        self.assertEqual(
            dict(
                exists=self.fs.exists(path=nonexistant),
                is_dir=self.fs.is_dir(path=nonexistant),
                is_file=self.fs.is_file(path=nonexistant),
                is_link=self.fs.is_link(path=nonexistant),
            ),
            dict(exists=False, is_dir=False, is_file=False, is_link=False),
        )
