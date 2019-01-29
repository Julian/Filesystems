import os.path

from pyrsistent import pvector
from zope.interface import implementer
import attr

from filesystems import _PY3, interfaces
from filesystems.exceptions import InvalidPath


if _PY3:
    basestring = bytes, str


@implementer(interfaces.Path)
@attr.s(these={"segments": attr.ib()}, init=False, repr=False, hash=True)
class Path(object):
    def __init__(self, *segments):
        self.segments = pvector(segments)

    def __div__(self, other):
        if not isinstance(other, basestring):  # FIXME: Unicode paths
            return NotImplemented
        return self.descendant(other)

    def __repr__(self):
        return "<Path {}>".format(self)

    def __str__(self):
        return os.sep + os.sep.join(self.segments)

    if _PY3:
        __truediv__ = __div__
        __fspath__ = __str__

    @classmethod
    def cwd(cls):
        return cls.from_string(os.getcwd())

    @classmethod
    def expanded(cls, path):
        return cls.from_string(os.path.expanduser(path))

    @classmethod
    def root(cls):
        return cls()

    @classmethod
    def from_string(cls, path):
        """
        Create a path out of an OS-specific string.
        """

        if not path:
            raise InvalidPath(path)

        drive, rest = os.path.splitdrive(path.rstrip(os.sep))
        split = rest.split(os.sep)
        if split[0]:
            return RelativePath(*split)
        return cls(*split[1:])

    def basename(self):
        return (self.segments or [""])[-1]

    def dirname(self):
        return str(self.parent())

    def heritage(self):
        """
        The (top-down) direct ancestors of this path, including itself.
        """

        segments = pvector()
        for segment in self.segments[:-1]:
            segments = segments.append(segment)
            yield self.__class__(*segments)
        yield self

    def descendant(self, *segments):
        return self.__class__(*self.segments.extend(segments))

    def parent(self):
        return self.__class__(*self.segments[:-1])

    def sibling(self, name):
        if not self.segments:
            raise ValueError("The root file path has no siblings.")
        return self.parent() / name

    def relative_to(self, path):
        """
        Resolve this path against another ``Path``.

        A ``Path`` is always absolute, and therefore always resolves to itself.
        """

        return self


@implementer(interfaces.Path)
@attr.s(these={"segments": attr.ib()}, init=False, repr=False, hash=True)
class RelativePath(object):
    def __init__(self, *segments):
        self.segments = pvector(segments)

    def __div__(self, other):
        if not isinstance(other, basestring):  # FIXME: Unicode paths
            return NotImplemented
        return self.descendant(other)

    def __repr__(self):
        return "<Path {}>".format(self)

    def __str__(self):
        return os.sep.join(self.segments)

    if _PY3:
        __truediv__ = __div__
        __fspath__ = __str__

    def basename(self):
        return (self.segments or [""])[-1]

    def dirname(self):
        return str(self.parent())

    def parent(self):
        return self.__class__(*self.segments[:-1])

    def heritage(self):
        """
        The (top-down) direct ancestors of this path, including itself.
        """

        segments = pvector()
        for segment in self.segments[:-1]:
            segments = segments.append(segment)
            yield self.__class__(*segments)
        yield self

    def descendant(self, *segments):
        return self.__class__(*self.segments.extend(segments))

    def sibling(self, name):
        return self.parent() / name

    def relative_to(self, path):
        """
        Resolve this path against another ``Path``.
        """

        return path.descendant(*self.segments)
