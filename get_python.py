import os
import subprocess
import sys


cache_root = 'cache'
pyenv_root = os.path.join(cache_root, 'pyenv')


def check_call(args, *pargs, **kwargs):
    args = list(args)
    kwargs.setdefault('check', True)
    print('Launching: ')
    for arg in args:
        print('    {}'.format(arg))

    return subprocess.check_call(args, *pargs, **kwargs)


def get_url(url, path):
    check_call(
        [
            'curl',
            '-L',
            '-o', path,
            url,
        ],
    )


def python_name_from_version(version):
    version = '.'.join(version.replace('-', '.').split('.')[:2])

    if version.startswith('pypy'):
        return version

    return 'python{}'.format(version)


def install_python_linux(version):
    archive_file = 'python_archive'
    url = (
        'https://s3.amazonaws.com'
        '/travis-python-archives/binaries/ubuntu/16.04/x86_64'
        '/python-{}.tar.bz2'.format(version)
    )

    get_url(url=url, path=archive_file)

    check_call(
        [
            'sudo',
            'tar',
            'xjf',
            archive_file,
            '--directory', '/',
        ],
    )

    return python_name_from_version(version)


def install_pyenv():
    pyenv_root_parent = os.path.dirname(pyenv_root)
    os.makedirs(pyenv_root_parent, exist_ok=True)

    pyenv_archive = 'pyenv_archive.zip'

    get_url(
        url='https://github.com/pyenv/pyenv/archive/master.zip',
        path=pyenv_archive,
    )

    check_call(['unzip', '-d', pyenv_root_parent, pyenv_archive])
    os.rename(
        src=os.path.join(pyenv_root_parent, 'pyenv-master'),
        dst=pyenv_root,
    )

    # TODO: mm, side affects
    os.environ['PYENV_ROOT'] = pyenv_root

    pyenv_path = os.path.join(pyenv_root, 'bin', 'pyenv')

    check_call([pyenv_path, 'rehash'])

    return pyenv_path


def install_python_darwin(version):
    pyenv_path = install_pyenv()
    check_call([pyenv_path, 'install', version])
    check_call([pyenv_path, 'global', version])

    return os.path.join(
        pyenv_root,
        'shims',
        python_name_from_version(version),
    )


def platform_dispatch(d, *args, **kwargs):
    for name, f in d.items():
        if sys.platform.startswith(name):
            return f(*args, **kwargs)
    else:
        raise Exception('Platform not supported: {}'.format(sys.platform))


def install_python(*args, **kwargs):
    d = {
        'linux': install_python_linux,
        'darwin': install_python_darwin,
        # 'win': install_python_windows,
    }

    return platform_dispatch(d, *args, **kwargs)


def get_virtualenv(version):
    url = 'https://github.com/pypa/virtualenv/archive/{}.zip'.format(version)

    path = 'virtualenv_archive'

    get_url(url=url, path=path)

    check_call(
        [
            'unzip',
            path,
        ],
    )

    return 'virtualenv-{}'.format(version)


def main():
    version = os.environ['PYTHON']
    python_path = install_python(version)

    virtualenv_path = get_virtualenv('16.2.0')

    env_path = '.venv'

    env = dict(os.environ)
    env['PYTHONPATH'] = virtualenv_path

    check_call(
        [
            python_path,
            '-m', 'virtualenv',
            env_path,
        ],
        env=env,
    )


main()
