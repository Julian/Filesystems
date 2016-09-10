def children(fs, path):
    return {path.descendant(p) for p in fs.listdir(path)}


def touch(fs, path):
    fs.open(path=path, mode="w").close()
