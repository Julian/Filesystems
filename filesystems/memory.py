from io import BytesIO
from uuid import uuid4

from characteristic import Attribute, attributes
from pyrsistent import m, pset

from filesystems import Path, common, exceptions


def _open_file(fs, path, mode):
    parent = path.parent()
    contents = fs._state.get(parent)
    if contents is None:
        raise exceptions.FileNotFound(path)

    if mode == "w" or mode == "wb":
        file = _BytesIOIsTerrible()
        fs._state = fs._state.set(parent, contents.set(path, file))
        return file

    file = contents.get(path)
    if file is None:
        raise exceptions.FileNotFound(path)
    return BytesIO(file._hereismyvalue)


def _remove_file(fs, path):
    parent = path.parent()
    contents = fs._state.get(parent)
    if contents is None:
        raise exceptions.FileNotFound(path)

    if path not in contents:
        raise exceptions.FileNotFound(path)

    fs._state = fs._state.set(parent, contents.remove(path))


def _temporary_directory(fs):
    # TODO: Maybe this isn't good enough.
    directory = Path(uuid4().hex)
    fs.create_directory(path=directory)
    return directory


def _create_directory(fs, path):
    if path in fs._state:
        raise exceptions.FileExists(path)
    fs._state = fs._state.set(path, m())


def _list_directory(fs, path):
    if path not in fs._state:
        raise exceptions.FileNotFound(path)
    # FIXME: Inefficient
    return pset(child.basename() for child in fs._state[path]) | pset(
        subdirectory.basename() for subdirectory in fs._state
        if subdirectory.parent() == path
    )


def _remove(fs, path):
    if path not in fs._state:
        raise exceptions.FileNotFound(path)
    fs._state = fs._state.remove(path)


def _remove_empty_directory(fs, path):
    if _list_directory(fs=fs, path=path):
        raise exceptions.DirectoryNotEmpty(path)
    _remove(fs=fs, path=path)


FS = common.create(
    name="MemoryFS",
    state=m(),

    open_file=_open_file,
    remove_file=_remove_file,

    create_directory=_create_directory,
    list_directory=_list_directory,
    remove_empty_directory=_remove_empty_directory,
    temporary_directory=_temporary_directory,

    remove=_remove,

    exists=lambda fs, path: (
        path in fs._state or path in fs._state.get(path.parent(), m())
    ),
    is_dir=lambda fs, path: path in fs._state,
    is_file=lambda fs, path: path in fs._state.get(path.parent(), m()),
    is_link=lambda fs, path: False,
)


class _BytesIOIsTerrible(BytesIO):
    def close(self):
        self._hereismyvalue = self.getvalue()
        super(_BytesIOIsTerrible, self).close()
