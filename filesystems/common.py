from fnmatch import fnmatch

from pyrsistent import pset
import attr


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

    open_file,
    create_file,
    remove_file,

    create_directory,
    list_directory,
    remove_empty_directory,
    temporary_directory,

    link,
    readlink,
    realpath,

    exists,
    is_dir,
    is_file,
    is_link,

    remove=_recursive_remove,

    state=lambda: None,
):
    """
    Create a new kind of filesystem.

    """

    return attr.s(hash=True)(
        type(
            name, (object,), dict(
                _state=attr.ib(default=attr.Factory(state), repr=False),

                create=create_file,
                open=lambda fs, path, mode="rb": open_file(
                    fs=fs, path=path, mode=mode,
                ),
                remove_file=remove_file,

                remove=remove,

                create_directory=create_directory,
                list_directory=list_directory,
                remove_empty_directory=remove_empty_directory,
                temporary_directory=temporary_directory,

                link=link,
                readlink=readlink,
                realpath=realpath,

                exists=exists,
                is_dir=is_dir,
                is_file=is_file,
                is_link=is_link,

                touch=_touch,
                children=_children,
                glob_children=_glob_children,
                contents_of=_open_and_read,
            ),
        ),
    )


def _children(fs, path):
    return pset(path.descendant(p) for p in fs.list_directory(path=path))


def _glob_children(fs, path, glob):
    return pset(
        path.descendant(p)
        for p in fs.list_directory(path=path)
        if fnmatch(p, glob)
    )


def _touch(fs, path):
    fs.open(path=path, mode="wb").close()


def _open_and_read(fs, path):
    with fs.open(path=path) as file:
        return file.read()
