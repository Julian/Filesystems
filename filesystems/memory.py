from io import BytesIO
from uuid import uuid4

from characteristic import Attribute, attributes
from pyrsistent import m

from filesystems import Path


@attributes(
    [Attribute(name="_contents", default_value=m(), exclude_from_repr=True)],
)
class FS(object):
    """
    An in-memory filesystem.

    """

    def open(self, path, mode="rb"):
        if mode == "w" or mode == "wb":
            # XXX: non-existant parent
            contents = _BytesIOIsTerrible()
            self._contents = self._contents.set(path, (contents, None))
            return contents

        contents, _ = self._contents[path]
        return BytesIO(contents._hereismyvalue)

    def listdir(self, path):
        # FIXME: Inefficient
        return {
            child.segments[-1] for child in self._contents
            if child.parent() == path
        }

    def remove(self, path):
        self._contents = self._contents.remove(path)

    def create_directory(self, path):
        self._contents = self._contents.set(path, (None, None))

    def temporary_directory(self):
        # TODO: Maybe this isn't good enough.
        directory = Path(uuid4().hex)
        self.create_directory(path=directory)
        return directory

    def exists(self, path):
        return path in self._contents

    def is_dir(self, path):
        if not self.exists(path):
            return False
        contents, _ = self._contents[path]
        return contents is None

    def is_file(self, path):
        return False

    def is_link(self, path):
        return False


class _BytesIOIsTerrible(BytesIO):
    def close(self):
        self._hereismyvalue = self.getvalue()
        super(_BytesIOIsTerrible, self).close()
