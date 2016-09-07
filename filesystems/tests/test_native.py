from unittest import TestCase

from filesystems import Path, native


class TestNative(TestCase):
    def test_it_opens_local_files(self):
        path = Path.from_string(__file__)
        fs = native.FS()
        with fs.open(path) as got, open(__file__) as expected:
            self.assertEqual(got.read(), expected.read())
