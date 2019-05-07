from zope.interface import Attribute, Interface

from filesystems import _PY3


class Filesystem(Interface):
    def create(path):
        pass

    def open(path, mode):
        pass

    def remove_file(path):
        pass

    def create_directory(path):
        pass

    def list_directory(path):
        pass

    def remove_empty_directory(path):
        pass

    def temporary_directory():
        pass

    def get_contents(path):
        pass

    def set_contents(path, contents):
        pass

    def create_with_contents(path, contents):
        pass

    def remove(path):
        pass

    def removing(path):
        pass

    def stat(path):
        pass

    def lstat(path):
        pass

    def link(source, to):
        pass

    def readlink(path):
        pass

    def realpath(path):
        pass

    def exists(path):
        pass

    def is_dir(path):
        pass

    def is_file(path):
        pass

    def is_link(path):
        pass

    def touch(path):
        pass

    def children(path):
        pass

    def glob_children(path, pattern):
        pass

    def bind(path):
        pass


class Path(Interface):

    segments = Attribute("The path segments that make up this path")

    def __str__():
        """
        Render the path as a string.
        """

    if _PY3:
        def __fspath__():
            """
            Render the path as a string.
            """

        def __truediv__(other):
            """
            Traverse to a child of this path.
            """
    else:
        def __div__(other):
            """
            Traverse to a child of this path.
            """

    def basename():
        """
        The tail component of this path.
        """

    def dirname():
        """
        The head components of this path.
        """

    def heritage():
        """
        The top-down set of this path's parents.
        """

    def descendant(*segments):
        """
        Traverse to a descendant of this path.
        """

    def parent():
        """
        Traverse to the parent of this path.
        """

    def sibling(name):
        """
        Traverse to a sibling of this path.
        """

    def relative_to(path):
        """
        Resolve a path relative to this one.
        """


class _BoundPath(Path, Interface):
    def create():
        pass

    def open(mode):
        pass

    def remove_file():
        pass

    def create_directory():
        pass

    def list_directory():
        pass

    def remove_empty_directory():
        pass

    def temporary_directory():
        pass

    def get_contents():
        pass

    def set_contents(contents):
        pass

    def create_with_contents(contents):
        pass

    def remove():
        pass

    def removing():
        pass

    def stat():
        pass

    def lstat():
        pass

    def link_from(path):
        pass

    def link_to(path):
        pass

    def readlink():
        pass

    def realpath():
        pass

    def exists():
        pass

    def is_dir():
        pass

    def is_file():
        pass

    def is_link():
        pass

    def touch():
        pass

    def children():
        pass

    def glob_children(pattern):
        pass
