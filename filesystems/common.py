from contextlib import contextmanager
from fnmatch import fnmatch
import stat

from pyrsistent import pset
import attr

from filesystems import _PY3, Path, exceptions


def _realpath(fs, path, seen=pset()):
    """
    .. warning::

        The ``os.path`` module's realpath does not error or warn about
        loops, but we do, following the behavior of GNU ``realpath(1)``!
    """

    real = Path.root()
    for segment in path.segments:
        current = real / segment
        seen = seen.add(current)
        while True:
            try:
                current = fs.readlink(current)
            except (exceptions.FileNotFound, exceptions.NotASymlink):
                break
            else:
                current = current.relative_to(real)
                if current in seen:
                    raise exceptions.SymbolicLoop(path)
                current = fs.realpath(current, seen=seen)
        real = current
    return real


def _recursive_remove(fs, path):
    """
    A recursive, non-atomic directory removal.
    """
    if not fs.is_link(path=path) and fs.is_dir(path=path):
        for child in fs.children(path=path):
            _recursive_remove(fs=fs, path=child)
        fs.remove_empty_directory(path=path)
    else:
        fs.remove_file(path=path)


def create(
    name,

    create_file,
    open_file,
    remove_file,

    create_directory,
    list_directory,
    remove_empty_directory,
    temporary_directory,

    stat,

    lstat,
    link,
    readlink,

    realpath=_realpath,
    remove=_recursive_remove,
):
    """
    Create a new kind of filesystem.
    """

    methods = dict(
        create=create_file,
        open=lambda fs, path, mode="r": open_file(
            fs=fs, path=path, mode=mode,
        ),
        remove_file=remove_file,

        create_directory=create_directory,
        list_directory=list_directory,
        remove_empty_directory=remove_empty_directory,
        temporary_directory=temporary_directory,

        get_contents=lambda fs, path, mode="": _get_contents(
            fs=fs, path=path, mode=mode,
        ),
        set_contents=lambda fs, path, contents, mode="": _set_contents(
            fs=fs, path=path, contents=contents, mode=mode,
        ),
        create_with_contents=_create_with_contents,

        remove=remove,
        removing=_removing,

        stat=stat,

        lstat=lstat,
        link=link,
        readlink=readlink,
        realpath=realpath,

        exists=_exists,
        is_dir=_is_dir,
        is_file=_is_file,
        is_link=_is_link,

        touch=_touch,

        children=_children,
        glob_children=_glob_children,
    )
    return attr.s(hash=True)(type(name, (object,), methods))


@contextmanager
def _removing(fs, path):
    try:
        yield path
    finally:
        fs.remove(path=path)


def _get_contents(fs, path, mode):
    with fs.open(path=path, mode="r" + mode) as file:
        return file.read()


def _set_contents(fs, path, contents, mode):
    with fs.open(path=path, mode="w" + mode) as file:
        file.write(contents)


def _create_with_contents(fs, path, contents):
    with fs.create(path=path) as file:
        file.write(contents)


def _children(fs, path):
    return pset(path / p for p in fs.list_directory(path=path))


def _glob_children(fs, path, glob):
    return pset(
        path / p
        for p in fs.list_directory(path=path)
        if fnmatch(p, glob)
    )


def _touch(fs, path):
    fs.open(path=path, mode="wb").close()


def _open_and_read(fs, path):
    with fs.open(path=path) as file:
        return file.read()


def _exists(fs, path):
    """
    Check that the given path exists on the filesystem.

    Note that unlike `os.path.exists`, we *do* propagate file system errors
    other than a non-existent path or non-existent directory component.

    E.g., should EPERM or ELOOP be raised, an exception will bubble up.
    """
    try:
        fs.stat(path)
    except (exceptions.FileNotFound, exceptions.NotADirectory):
        return False
    return True


def _is_dir(fs, path):
    """
    Check that the given path is a directory.

    Note that unlike `os.path.isdir`, we *do* propagate file system errors
    other than a non-existent path or non-existent directory component.

    E.g., should EPERM or ELOOP be raised, an exception will bubble up.
    """

    try:
        return stat.S_ISDIR(fs.stat(path).st_mode)
    except exceptions.FileNotFound:
        return False


def _is_file(fs, path):
    """
    Check that the given path is a file.

    Note that unlike `os.path.isfile`, we *do* propagate file system errors
    other than a non-existent path or non-existent directory component.

    E.g., should EPERM or ELOOP be raised, an exception will bubble up.
    """
    try:
        return stat.S_ISREG(fs.stat(path).st_mode)
    except exceptions.FileNotFound:
        return False


def _is_link(fs, path):
    """
    Check that the given path is a symbolic link.

    Note that unlike `os.path.islink`, we *do* propagate file system errors
    other than a non-existent path or non-existent directory component.

    E.g., should EPERM or ELOOP be raised, an exception will bubble up.
    """

    try:
        return stat.S_ISLNK(fs.lstat(path).st_mode)
    except exceptions.FileNotFound:
        return False


@attr.s(frozen=True)
class _FileMode(object):
    activity = attr.ib(default="r")
    mode = attr.ib(
        default='',
        converter=lambda x: x if x != "" else ("t" if _PY3 else "b"),
    )
    read = attr.ib()
    write = attr.ib()
    append = attr.ib()
    text = attr.ib()
    binary = attr.ib()

    @read.default
    def read_default(self):
        return self.activity == "r"

    @write.default
    def write_default(self):
        return self.activity == "w"

    @append.default
    def append_default(self):
        return self.activity == "a"

    @text.default
    def text_default(self):
        return self.mode == "t"

    @binary.default
    def binary_default(self):
        return self.mode == "b"

    @activity.validator
    def activity_validator(self, attribute, value):
        options = ("r", "w", "a")

        if value not in options:
            raise exceptions.InvalidMode(
                "Mode must start with one of {} but found {}".format(
                    repr(options),
                    repr(value),
                )
            )

    @mode.validator
    def _(self, attribute, value):
        options = ("b", "t")

        if value not in options:
            raise exceptions.InvalidMode(
                "Mode must start with one of {} but found {}".format(
                    repr(options),
                    repr(value),
                )
            )

    def io_open_string(self):
        return self.activity + self.mode


def _parse_mode(mode):
    parameters = {}
    first = mode[:1]
    rest = mode[1:]

    if len(first) > 0:
        parameters["activity"] = first

        if len(rest) > 0:
            parameters["mode"] = rest

    return _FileMode(**parameters)
