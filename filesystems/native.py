import os
import tempfile

from filesystems import Path, common, exceptions


def _open_file(fs, path, mode):
    try:
        return open(str(path), mode)
    except (IOError, OSError) as error:
        if error.errno == exceptions.FileNotFound.errno:
            raise exceptions.FileNotFound(path)
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


FS = common.create(
    name="NativeFS",

    open_file=_open_file,
    remove_file=_remove_file,

    create_directory=_create_directory,
    list_directory=_list_directory,
    remove_empty_directory=_remove_empty_directory,
    temporary_directory=lambda fs: Path.from_string(tempfile.mkdtemp()),

    exists=lambda fs, path: os.path.exists(str(path)),
    is_dir=lambda fs, path: os.path.isdir(str(path)),
    is_file=lambda fs, path: os.path.isfile(str(path)),
    is_link=lambda fs, path: os.path.islink(str(path)),
)
