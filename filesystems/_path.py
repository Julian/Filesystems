import os

from pyrsistent import pvector
import attr


@attr.s(these={"segments": attr.ib()}, init=False)
class Path(object):
    def __init__(self, *segments):
        self.segments = pvector(segments)

    def __str__(self):
        return os.sep + os.sep.join(self.segments)

    @classmethod
    def cwd(cls):
        return cls.from_string(os.getcwd())

    @classmethod
    def root(cls):
        return cls()

    @classmethod
    def from_string(cls, path):
        """
        Create a path out of an OS-specific string.

        """

        segments = os.path.abspath(path).lstrip(os.sep).split(os.sep)
        return cls(*segments)

    def basename(self):
        return (self.segments or [""])[-1]

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
