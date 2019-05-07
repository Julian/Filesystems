from contextlib import contextmanager
from fnmatch import fnmatch
import stat

from pyrsistent import pset
from zope.interface import implementer
import attr

from filesystems import _PY3, _path as _path_module, exceptions, interfaces


def _realpath(fs, path, seen=pset()):
    """
    .. warning::

        The ``os.path`` module's realpath does not error or warn about
        loops, but we do, following the behavior of GNU ``realpath(1)``!
    """

    real = _path_module.Path.root()
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

        get_contents=_get_contents,
        set_contents=_set_contents,
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

        bind=lambda self, path: _BoundPath(path=path, fs=self),
    )
    cls = attr.s(hash=True)(type(name, (object,), methods))
    return implementer(interfaces.Filesystem)(cls)


@contextmanager
def _removing(fs, path):
    try:
        yield path
    finally:
        fs.remove(path=path)


def _get_contents(fs, path):
    with fs.open(path=path) as file:
        return file.read()


def _set_contents(fs, path, contents):
    with fs.open(path=path, mode="w") as file:
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


@implementer(interfaces._BoundPath)
@attr.s(hash=True)
class _BoundPath(object):
    """
    A path bound to a specific filesystem.
    """

    _fs = attr.ib()
    _path = attr.ib()

    __div__ = _path_module.__div__
    basename = _path_module.basename
    dirname = _path_module.dirname

    @property
    def segments(self):
        return self._path.segments

    def heritage(self):
        return (
            self.__class__(fs=self._fs, path=path)
            for path in self._path.heritage()
        )

    def parent(self):
        return self.__class__(fs=self._fs, path=self._path.parent())

    def descendant(self, *segments):
        descendant = self._path.descendant(*segments)
        return self.__class__(fs=self._fs, path=descendant)

    def sibling(self, name):
        return self._fs.bind(path=self._path.sibling(name))

    def relative_to(self, path):
        return self._fs.bind(path=self._path.relative_to(path=path))

    def create(self):
        return self._fs.create(path=self._path)

    def open(self, mode):
        return self._fs.open(path=self._path, mode=mode)

    def remove_file(self):
        return self._fs.remove_file(path=self._path)

    def create_directory(self):
        return self._fs.create_directory(path=self._path)

    def list_directory(self):
        return self._fs.list_directory(path=self._path)

    def remove_empty_directory(self):
        return self._fs.remove_empty_directory(path=self._path)

    def temporary_directory(self):
        return self._fs.temporary_directory(path=self._path)

    def get_contents(self):
        return self._fs.get_contents(path=self._path)

    def set_contents(self, contents):
        return self._fs.set_contents(path=self._path, contents=contents)

    def create_with_contents(self, contents):
        return self._fs.create_with_contents(
            path=self._path,
            contents=contents,
        )

    def remove(self):
        return self._fs.remove(path=self._path)

    def removing(self):
        return self._fs.removing(path=self._path)

    def stat(self):
        return self._fs.stat(path=self._path)

    def lstat(self):
        return self._fs.lstat(path=self._path)

    def link_from(self, path):
        return self._fs.link(source=path, to=self._path)

    def link_to(self, path):
        return self._fs.link(source=self._path, to=path)

    def readlink(self):
        return self._fs.link(path=self._path)

    def realpath(self):
        return self._fs.realpath(path=self._path)

    def exists(self):
        return self._fs.exists(path=self._path)

    def is_dir(self):
        return self._fs.is_dir(path=self._path)

    def is_file(self):
        return self._fs.is_file(path=self._path)

    def is_link(self):
        return self._fs.is_link(path=self._path)

    def touch(self):
        return self._fs.touch(path=self._path)

    def children(self):
        return self._fs.children(path=self._path)

    def glob_children(self, pattern):
        return self._fs.glob_children(path=self._path, pattern=pattern)


def _parse_mode(mode):
    parameters = {}
    first = mode[:1]
    rest = mode[1:]

    if len(first) > 0:
        parameters["activity"] = first

        if len(rest) > 0:
            parameters["mode"] = rest

    return _FileMode(**parameters)
