from filesystems import Path, common, exceptions


def FS(on, path):

    parent = path

    def wrap(fn):
        def wrapper(fs, path, *args, **kwargs):
            return fn(path=parent.descendant(*path.segments), *args, **kwargs)
        return wrapper

    return common.create(
        name="DownwardFS",

        create_file=wrap(on.create),
        open_file=wrap(on.open),
        remove_file=wrap(on.remove),

        create_directory=wrap(on.create_directory),
        list_directory=wrap(on.list_directory),
        remove_empty_directory=wrap(on.remove_empty_directory),
        temporary_directory=wrap(on.temporary_directory),

        link=wrap(on.link),
        readlink=wrap(on.readlink),
        realpath=wrap(on.realpath),

        exists=wrap(on.exists),
        is_dir=wrap(on.is_dir),
        is_file=wrap(on.is_file),
        is_link=wrap(on.is_link),
    )()
