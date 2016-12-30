from characteristic import Attribute, attributes


def recursive_remove(fs, path):
    """
    A recursive, non-atomic directory removal.

    """

    if fs.is_dir(path=path) and not fs.is_link(path=path):
        for child in fs.children(path=path):
            recursive_remove(fs=fs, path=child)
        fs.remove_empty_directory(str(path))
    else:
        fs.remove_file(str(path))


def create(
    name,

    open_file,
    remove_file,

    create_directory,
    list_directory,
    remove_empty_directory,
    temporary_directory,

    exists,
    is_dir,
    is_file,
    is_link,

    remove=recursive_remove,

    state=None,
):
    """
    Create a new kind of filesystem.

    """

    return attributes([Attribute(name="_state", default_value=state)])(
        type(
            name, (object,), dict(
                open=lambda fs, path, mode="rb": open_file(
                    fs=fs, path=path, mode=mode,
                ),
                remove_file=remove_file,

                remove=remove,

                create_directory=create_directory,
                list_directory=list_directory,
                remove_empty_directory=remove_empty_directory,
                temporary_directory=temporary_directory,

                exists=exists,
                is_dir=is_dir,
                is_file=is_file,
                is_link=is_link,

                touch=_touch,
                children=_children,
            ),
        ),
    )


def _children(fs, path):
    return {path.descendant(p) for p in fs.list_directory(path=path)}


def _touch(fs, path):
    fs.open(path=path, mode="wb").close()
