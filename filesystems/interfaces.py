"""
Interface definitions for filesystems.
"""

from zope.interface import Interface


class Path(Interface):
    """
    The interface all path objects adhere to.
    """

    def __str__():
        """
        Render the path as a string.
        """

    def __fspath__():
        """
        Render the path as a string.
        """

    def __truediv__(other):  # noqa: PLE0302
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
