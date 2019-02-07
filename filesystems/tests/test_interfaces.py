from unittest import TestCase

from pyrsistent import pset

from filesystems import interfaces


class TestBoundPath(TestCase):
    def test_it_has_all_the_filesystem_methods(self):
        unioned = pset(interfaces.Path).update(interfaces.Filesystem)
        methods = unioned.remove(
            "bind"
        ).remove(
            "link",
        ).add(
            "link_from",
        ).add(
            "link_to",
        )
        self.assertEqual(pset(interfaces._BoundPath), methods)
