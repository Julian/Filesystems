from io import BytesIO, TextIOWrapper
from uuid import uuid4

from pyrsistent import pmap, pset
import attr

from filesystems import Path, common, exceptions


@attr.s(hash=True)
class _State(object):
    """
    The state of a memory filesystem.

    Includes its file contents and tree state.
    """

    _tree = pmap([(Path.root(), pmap())])
    _links = pmap()

    def create_file(self, fs, path):
        if fs.exists(path=path) or fs.is_link(path=path):
            raise exceptions.FileExists(path)

        path = fs.realpath(path=path)
        parent = path.parent()
        contents = self._tree.get(parent)
        if contents is None:
            raise exceptions.FileNotFound(path)
        file = _BytesIOIsTerrible()
        self._tree = self._tree.set(parent, contents.set(path, file))
        return file

    def open_file(self, fs, path, mode):
        mode = common._parse_mode(mode)

        path = fs.realpath(path=path)

        parent = path.parent()
        contents = self._tree.get(parent)
        if contents is None:
            raise exceptions.FileNotFound(path)

        if mode.write:
            file = _BytesIOIsTerrible()
            self._tree = self._tree.set(parent, contents.set(path, file))
            if mode.text:
                file = TextIOWrapper(file)
            return file

        file = contents.get(path)

        if mode.append:
            combined = _BytesIOIsTerrible()

            if file is not None:
                combined.write(file._hereismyvalue)

            self._tree = self._tree.set(parent, contents.set(path, combined))

            if mode.text:
                combined = TextIOWrapper(combined)

            return combined
        elif file is None:
            raise exceptions.FileNotFound(path)
        else:
            file = _BytesIOIsTerrible(file._hereismyvalue)

            if mode.text:
                file = TextIOWrapper(file)

            return file

    def remove_file(self, fs, path):
        parent = path.parent()
        contents = self._tree.get(parent)
        if contents is None:
            raise exceptions.FileNotFound(path)

        if path not in contents:
            raise exceptions.FileNotFound(path)

        self._tree = self._tree.set(parent, contents.remove(path))

    def create_directory(self, fs, path):
        if fs.exists(path=path):
            raise exceptions.FileExists(path)

        parent = path.parent()
        if not fs.exists(path=parent):
            raise exceptions.FileNotFound(parent)

        self._tree = self._tree.set(fs.realpath(path=path), pmap())

    def list_directory(self, fs, path):
        if fs.is_file(path=path):
            raise exceptions.NotADirectory(path)
        elif path not in self._tree:
            raise exceptions.FileNotFound(path)

        # FIXME: Inefficient
        return pset(child.basename() for child in self._tree[path]) | pset(
            subdirectory.basename() for subdirectory in self._tree
            if subdirectory.parent() == path
            and subdirectory != path
        )

    def remove_empty_directory(self, fs, path):
        if fs.list_directory(path=path):
            raise exceptions.DirectoryNotEmpty(path)
        self._tree = self._tree.remove(path)

    def temporary_directory(self, fs):
        # TODO: Maybe this isn't good enough.
        directory = Path(uuid4().hex)
        fs.create_directory(path=directory)
        return directory

    def remove(self, fs, path):
        if fs.is_link(path=path):
            self._links = self._links.remove(path)
        elif path not in self._tree:
            raise exceptions.FileNotFound(path)

    def link(self, fs, source, to):
        if fs.exists(path=to) or fs.is_link(path=to):
            raise exceptions.FileExists(to)

        real = fs.realpath(to)
        parent = real.parent()
        if not fs.exists(path=parent):
            raise exceptions.FileNotFound(parent)
        elif not fs.is_dir(path=parent):
            raise exceptions.NotADirectory(parent)

        self._tree = self._tree.set(parent, self._tree[parent].set(real, None))
        self._links = self._links.set(to, source)

    def readlink(self, fs, path):
        value = self._links.get(path)
        if value is None:
            if self._exists(path=path):
                raise exceptions.NotASymlink(path)
            else:
                raise exceptions.FileNotFound(path)
        return value

    def exists(self, fs, path):
        return fs.is_file(path=path) or fs.is_dir(path=path)

    def is_dir(self, fs, path):
        return self._is_dir(path=fs.realpath(path=path))

    def is_file(self, fs, path):
        return self._is_file(path=fs.realpath(path=path))

    def _exists(self, path):
        return self._is_file(path=path) or self._is_dir(path=path)

    def _is_dir(self, path):
        return path in self._tree

    def _is_file(self, path):
        return path in self._tree.get(path.parent(), pmap())

    def is_link(self, fs, path):
        return path in self._links


@staticmethod
def FS():
    state = _State()
    return common.create(
        name="MemoryFS",
        create_file=_fs(state.create_file),
        open_file=_fs(state.open_file),
        remove_file=_fs(state.remove_file),

        create_directory=_fs(state.create_directory),
        list_directory=_fs(state.list_directory),
        remove_empty_directory=_fs(state.remove_empty_directory),
        temporary_directory=_fs(state.temporary_directory),

        link=_fs(state.link),
        readlink=_fs(state.readlink),

        exists=_fs(state.exists),
        is_dir=_fs(state.is_dir),
        is_file=_fs(state.is_file),
        is_link=_fs(state.is_link),
    )()


def _fs(fn):
    """
    Bind a function to pass along the filesystem itself.
    """
    return lambda fs, *args, **kwargs: fn(fs, *args, **kwargs)


class _BytesIOIsTerrible(BytesIO):
    def close(self):
        self._hereismyvalue = self.getvalue()
        super(_BytesIOIsTerrible, self).close()
