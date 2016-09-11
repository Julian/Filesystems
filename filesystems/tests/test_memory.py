from unittest import TestCase

from filesystems import Path, memory
from filesystems.tests.common import TestFS


class TestMemory(TestFS, TestCase):
    FS = memory.FS
