import os

from characteristic import Attribute, attributes
from pyrsistent import pvector


@attributes(
    [Attribute(name="segments", exclude_from_init=True)],
)
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

    def descendant(self, *segments):
        return self.__class__(*self.segments.extend(segments))

    def parent(self):
        return self.__class__(*self.segments[:-1])
