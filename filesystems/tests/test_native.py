from unittest import TestCase

from filesystems import native
from filesystems.tests.common import TestFS


class TestNative(TestFS, TestCase):
    FS = native.FS
