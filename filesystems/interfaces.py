from zope.interface import Interface

from filesystems import _PY3


class Path(Interface):
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
