from io import BytesIO
from uuid import uuid4

from pyrsistent import pmap, pset
import attr

from filesystems import Path, common, exceptions


@attr.s
class _State(object):
    """
    The state of a memory filesystem.

    Includes its file contents and tree state.

    """

    _tree = pmap([(Path.root(), pmap())])
    _links = pmap()

    def open_file(self, path, mode):
        path = self.realpath(path=path)

        parent = path.parent()
        contents = self._tree.get(parent)
        if contents is None:
            raise exceptions.FileNotFound(path)

        if mode == "w" or mode == "wb":
            file = _BytesIOIsTerrible()
            self._tree = self._tree.set(parent, contents.set(path, file))
            return file

        file = contents.get(path)
        if file is None:
            raise exceptions.FileNotFound(path)
        return BytesIO(file._hereismyvalue)

    def remove_file(self, path):
        parent = path.parent()
        contents = self._tree.get(parent)
        if contents is None:
            raise exceptions.FileNotFound(path)

        if path not in contents:
            raise exceptions.FileNotFound(path)

        self._tree = self._tree.set(parent, contents.remove(path))

    def create_directory(self, path):
        if self.exists(path=path):
            raise exceptions.FileExists(path)
        self._tree = self._tree.set(path, pmap())

    def list_directory(self, path):
        if self.is_file(path=path):
            raise exceptions.NotADirectory(path)
        elif path not in self._tree:
            raise exceptions.FileNotFound(path)

        # FIXME: Inefficient
        return pset(child.basename() for child in self._tree[path]) | pset(
            subdirectory.basename() for subdirectory in self._tree
            if subdirectory.parent() == path
        )

    def remove_empty_directory(self, path):
        if self.list_directory(path=path):
            raise exceptions.DirectoryNotEmpty(path)
        self.remove(path=path)

    def temporary_directory(self):
        # TODO: Maybe this isn't good enough.
        directory = Path(uuid4().hex)
        self.create_directory(path=directory)
        return directory

    def remove(self, path):
        if path not in self._tree:
            raise exceptions.FileNotFound(path)
        self._tree = self._tree.remove(path)

    def link(self, source, to):
        self._tree = self._tree_with(path=to)
        self._links = self._links.set(to, source)

    def realpath(self, path):
        real = Path.root()
        for segment in path.segments:
            seen = current, = {real.descendant(segment)}
            while self.is_link(path=current):
                current = self._links[current]
                if current in seen:
                    raise exceptions.SymbolicLoop(current)
                seen.add(current)
            real = current
        return real

        seen = {path}
        while self.is_link(path):
            path = self._links[path]
            if path in seen:
                raise exceptions.SymbolicLoop(path)
            seen.add(path)
        return path

    def exists(self, path):
        return self.is_file(path=path) or self.is_dir(path=path)

    def is_dir(self, path):
        return self.realpath(path=path) in self._tree

    def is_file(self, path):
        real = self.realpath(path=path)
        return real in self._tree.get(real.parent(), pmap())

    def is_link(self, path):
        return path in self._links

    def _tree_with(self, path):
        parent = path.parent()
        if parent not in self._tree:
            raise exceptions.FileNotFound(parent)
        return self._tree.set(parent, self._tree[parent].set(path, None))


FS = common.create(
    name="MemoryFS",
    state=_State(),

    open_file=lambda fs, *args, **kw: fs._state.open_file(*args, **kw),
    remove_file=lambda fs, *args, **kw: fs._state.remove_file(*args, **kw),

    create_directory=(
        lambda fs, *args, **kw: fs._state.create_directory(*args, **kw)
    ),
    list_directory=(
        lambda fs, *args, **kw: fs._state.list_directory(*args, **kw)
    ),
    remove_empty_directory=(
        lambda fs, *args, **kw: fs._state.remove_empty_directory(*args, **kw)
    ),
    temporary_directory=(
        lambda fs, *args, **kw: fs._state.temporary_directory(*args, **kw)
    ),

    link=lambda fs, *args, **kw: fs._state.link(*args, **kw),
    realpath=lambda fs, *args, **kw: fs._state.realpath(*args, **kw),

    remove=lambda fs, *args, **kw: fs._state.remove(*args, **kw),

    exists=lambda fs, *args, **kw: fs._state.exists(*args, **kw),
    is_dir=lambda fs, *args, **kw: fs._state.is_dir(*args, **kw),
    is_file=lambda fs, *args, **kw: fs._state.is_file(*args, **kw),
    is_link=lambda fs, *args, **kw: fs._state.is_link(*args, **kw),
)


class _BytesIOIsTerrible(BytesIO):
    def close(self):
        self._hereismyvalue = self.getvalue()
        super(_BytesIOIsTerrible, self).close()
