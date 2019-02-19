from io import BytesIO, TextIOWrapper
from uuid import uuid4
import os
import stat

from pyrsistent import pmap, pset
import attr

from filesystems import Path, common, exceptions


class _BytesIOIsTerrible(BytesIO):
    def __repr__(self):
        return "<BytesIOIsTerrible contents={!r}>".format(self.bytes)

    def close(self):
        self._hereismyvalue = self.getvalue()
        super(_BytesIOIsTerrible, self).close()

    @property
    def bytes(self):
        if self.closed:
            return self._hereismyvalue
        return self.getvalue()


def FS():
    return _State().FS(name="MemoryFS")


def _fs(fn):
    """
    Eat the fs argument.
    """
    return lambda fs, *args, **kwargs: fn(*args, **kwargs)


@attr.s(hash=True)
class _File(object):
    """
    A file.
    """

    _name = attr.ib()
    _parent = attr.ib(repr=False)
    _contents = attr.ib(factory=_BytesIOIsTerrible)

    def __getitem__(self, name):
        return _FileChild(parent=self._parent)

    def create_directory(self, path):
        raise exceptions.FileExists(path)

    def list_directory(self, path):
        raise exceptions.NotADirectory(path)

    def remove_empty_directory(self, path):
        raise exceptions.NotADirectory(path)

    def create_file(self, path):
        raise exceptions.FileExists(path)

    def open_file(self, path, mode):
        if mode.read:
            file = _BytesIOIsTerrible(self._contents.bytes)
        elif mode.write:
            self._contents = _BytesIOIsTerrible()
            file = self._contents
        else:
            original, self._contents = self._contents, _BytesIOIsTerrible()
            self._contents.write(original.bytes)
            file = self._contents

        if mode.text:
            return TextIOWrapper(file)
        return file

    def remove_file(self, path):
        del self._parent[self._name]

    def link(self, source, to, fs, state):
        raise exceptions.FileExists(to)

    def readlink(self, path):
        raise exceptions.NotASymlink(path)

    def stat(self, path):
        return os.stat_result((stat.S_IFREG,) + (0,) * 9)

    lstat = stat


@attr.s(hash=True)
class _FileChild(object):
    """
    The attempted "child" of a file, which well, shouldn't have children.
    """

    _parent = attr.ib()

    def __getitem__(self, name):
        return self

    def create_directory(self, path):
        raise exceptions.NotADirectory(path.parent())

    def list_directory(self, path):
        raise exceptions.NotADirectory(path)

    def remove_empty_directory(self, path):
        raise exceptions.NotADirectory(path)

    def create_file(self, path):
        raise exceptions.NotADirectory(path)

    def open_file(self, path, mode):
        raise exceptions.NotADirectory(path)

    def remove_file(self, path):
        raise exceptions.NotADirectory(path)

    def link(self, source, to, fs, state):
        raise exceptions.NotADirectory(to.parent())

    def readlink(self, path):
        raise exceptions.NotADirectory(path)

    def stat(self, path):
        raise exceptions.NotADirectory(path)

    lstat = stat


@attr.s(hash=True)
class _Directory(object):
    """
    A directory.
    """

    _name = attr.ib()
    _parent = attr.ib(repr=False)
    _children = attr.ib(default=pmap())

    @classmethod
    def root(cls):
        root = cls(name="", parent=None)
        root._parent = root
        return root

    def __getitem__(self, name):
        return self._children.get(
            name,
            _DirectoryChild(name=name, parent=self),
        )

    def __setitem__(self, name, node):
        self._children = self._children.set(name, node)

    def __delitem__(self, name):
        self._children = self._children.remove(name)

    def create_directory(self, path):
        raise exceptions.FileExists(path)

    def list_directory(self, path):
        return pset(self._children)

    def remove_empty_directory(self, path):
        if self._children:
            raise exceptions.DirectoryNotEmpty(path)
        del self._parent[self._name]

    def create_file(self, path):
        raise exceptions.FileExists(path)

    def open_file(self, path, mode):
        raise exceptions.IsADirectory(path)

    def remove_file(self, path):
        raise exceptions._UnlinkNonFileError(path)

    def link(self, source, to, fs, state):
        raise exceptions.FileExists(to)

    def readlink(self, path):
        raise exceptions.NotASymlink(path)

    def stat(self, path):
        return os.stat_result((stat.S_IFDIR,) + (0,) * 9)

    lstat = stat


@attr.s(hash=True)
class _DirectoryChild(object):
    """
    A node that doesn't exist, but is within an existing directory.

    It therefore *could* exist if asked to create itself.
    """

    _name = attr.ib()
    _parent = attr.ib(repr=False)

    def __getitem__(self, name):
        return _NO_SUCH_ENTRY

    def create_directory(self, path):
        self._parent[self._name] = _Directory(
            name=self._name,
            parent=self._parent,
        )

    def list_directory(self, path):
        raise exceptions.FileNotFound(path)

    def remove_empty_directory(self, path):
        raise exceptions.FileNotFound(path)

    def create_file(self, path):
        file = self._parent[self._name] = _File(
            name=self._name,
            parent=self._parent,
        )
        return file.open_file(path=path, mode=common._FileMode(activity="w"))

    def open_file(self, path, mode):
        if mode.read:
            raise exceptions.FileNotFound(path)
        else:
            file = self._parent[self._name] = _File(
                name=self._name,
                parent=self._parent,
            )
            return file.open_file(path=path, mode=mode)

    def remove_file(self, path):
        raise exceptions.FileNotFound(path)

    def link(self, source, to, fs, state):
        self._parent[self._name] = _Link(
            name=self._name,
            parent=self._parent,
            source=source,
            entry_at=lambda path=source: state[fs.realpath(path=path)],
        )

    def readlink(self, path):
        raise exceptions.FileNotFound(path)

    def stat(self, path):
        raise exceptions.FileNotFound(path)

    lstat = stat


@attr.s(hash=True)
class _Link(object):

    _name = attr.ib()
    _parent = attr.ib(repr=False)
    _source = attr.ib()
    _entry_at = attr.ib(repr=False)

    def __getitem__(self, name):
        return self._entry_at()[name]

    def create_directory(self, path):
        raise exceptions.FileExists(path)

    def list_directory(self, path):
        return self._entry_at(path=path).list_directory(path=path)

    def remove_empty_directory(self, path):
        raise exceptions.NotADirectory(path)

    def create_file(self, path):
        raise exceptions.FileExists(path)

    def open_file(self, path, mode):
        return self._entry_at(path=path).open_file(path=path, mode=mode)

    def remove_file(self, path):
        del self._parent[self._name]

    def link(self, source, to, fs, state):
        raise exceptions.FileExists(to)

    def readlink(self, path):
        return self._source

    def stat(self, path):
        return self._entry_at(path=path).stat(path=path)

    def lstat(self, path):
        return os.stat_result((stat.S_IFLNK,) + (0,) * 9)


@attr.s(hash=True)
class _NoSuchEntry(object):
    """
    A non-existent node that also cannot be created.

    It has no existing parent. What a shame.
    """

    def __getitem__(self, name):
        return self

    def create_directory(self, path):
        raise exceptions.FileNotFound(path.parent())

    def list_directory(self, path):
        raise exceptions.FileNotFound(path)

    def remove_empty_directory(self, path):
        raise exceptions.FileNotFound(path)

    def create_file(self, path):
        raise exceptions.FileNotFound(path)

    def open_file(self, path, mode):
        raise exceptions.FileNotFound(path)

    def remove_file(self, path):
        raise exceptions.FileNotFound(path)

    def link(self, source, to, fs, state):
        raise exceptions.FileNotFound(to.parent())

    def readlink(self, path):
        raise exceptions.FileNotFound(path)

    def stat(self, path):
        raise exceptions.FileNotFound(path)

    lstat = stat


_NO_SUCH_ENTRY = _NoSuchEntry()


@attr.s(hash=True)
class _State(object):

    _root = attr.ib(factory=_Directory.root)

    def __getitem__(self, path):
        """
        Retrieve the Node at the given path.
        """
        node = self._root
        for segment in path.segments:
            node = node[segment]
        return node

    def FS(self, name):
        return common.create(
            name=name,

            create_file=_fs(self.create_file),
            open_file=_fs(self.open_file),
            remove_file=_fs(self.remove_file),

            create_directory=_fs(self.create_directory),
            list_directory=_fs(self.list_directory),
            remove_empty_directory=_fs(self.remove_empty_directory),
            temporary_directory=_fs(self.temporary_directory),

            stat=_fs(self.stat),

            lstat=_fs(self.lstat),
            link=lambda fs, *args, **kwargs: self.link(*args, fs=fs, **kwargs),
            readlink=_fs(self.readlink),
        )()

    def create_directory(self, path):
        self[path].create_directory(path=path)

    def list_directory(self, path):
        return self[path].list_directory(path=path)

    def remove_empty_directory(self, path):
        return self[path].remove_empty_directory(path=path)

    def temporary_directory(self):
        # TODO: Maybe this isn't good enough.
        directory = Path(uuid4().hex)
        self.create_directory(path=directory)
        return directory

    def create_file(self, path):
        return self[path].create_file(path=path)

    def open_file(self, path, mode):
        mode = common._parse_mode(mode=mode)
        return self[path].open_file(path=path, mode=mode)

    def remove_file(self, path):
        self[path].remove_file(path=path)

    def link(self, source, to, fs):
        self[to].link(fs=fs, source=source, to=to, state=self)

    def readlink(self, path):
        return self[path].readlink(path=path)

    def lstat(self, path):
        return self[path].lstat(path=path)

    def stat(self, path):
        return self[path].stat(path=path)
