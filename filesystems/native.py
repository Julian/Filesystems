import os
import tempfile

from filesystems import Path, common, exceptions


def _open_file(fs, path, mode):
    try:
        return open(str(path), mode)
    except (IOError, OSError) as error:
        if error.errno == exceptions.FileNotFound.errno:
            raise exceptions.FileNotFound(path)
        elif error.errno == exceptions.SymbolicLoop.errno:
            raise exceptions.SymbolicLoop(path)
        raise


def _remove_file(fs, path):
    try:
        os.remove(str(path))
    except (IOError, OSError) as error:
        if error.errno == exceptions.FileNotFound.errno:
            raise exceptions.FileNotFound(path)
        raise


def _create_directory(fs, path):
    try:
        os.mkdir(str(path))
    except (IOError, OSError) as error:
        if error.errno == exceptions.FileExists.errno:
            raise exceptions.FileExists(path)
        raise


def _list_directory(fs, path):
    try:
        return os.listdir(str(path))
    except (IOError, OSError) as error:
        if error.errno == exceptions.FileNotFound.errno:
            raise exceptions.FileNotFound(path)
        elif error.errno == exceptions.NotADirectory.errno:
            raise exceptions.NotADirectory(path)
        raise


def _remove_empty_directory(fs, path):
    try:
        os.rmdir(str(path))
    except (IOError, OSError) as error:
        if error.errno == exceptions.DirectoryNotEmpty.errno:
            raise exceptions.DirectoryNotEmpty(path)
        elif error.errno == exceptions.FileNotFound.errno:
            raise exceptions.FileNotFound(path)
        raise


def _link(fs, source, to):
    try:
        os.symlink(str(source), str(to))
    except (IOError, OSError) as error:
        if error.errno == exceptions.FileNotFound.errno:
            raise exceptions.FileNotFound(to.parent())
        raise


def _realpath(fs, path):
    """
    .. warning::

        The ``os.path`` module's realpath does not error or warn about
        loops, but we do, following the behavior of GNU ``realpath(1)``!

    """

    real = Path.root()
    for segment in path.segments:
        seen = current, = {str(real.descendant(segment))}
        while os.path.islink(current):
            current = os.readlink(current)
            if current in seen:
                raise exceptions.SymbolicLoop(current)
            seen.add(current)
        real = Path.from_string(current)
    return real


FS = common.create(
    name="NativeFS",

    open_file=_open_file,
    remove_file=_remove_file,

    create_directory=_create_directory,
    list_directory=_list_directory,
    remove_empty_directory=_remove_empty_directory,
    temporary_directory=lambda fs: Path.from_string(tempfile.mkdtemp()),

    link=_link,
    realpath=_realpath,

    exists=lambda fs, path: os.path.exists(str(path)),
    is_dir=lambda fs, path: os.path.isdir(str(path)),
    is_file=lambda fs, path: os.path.isfile(str(path)),
    is_link=lambda fs, path: os.path.islink(str(path)),
)
