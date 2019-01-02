import os
import subprocess
import sys


def check_call(args, *pargs, **kwargs):
    args = list(args)
    print('Launching: ')
    for arg in args:
        print('    {}'.format(arg))

    return subprocess.check_call(args, *pargs, **kwargs)


def get_url(url, path):
    check_call(
        [
            'curl',
            '-o', path,
            url,
        ],
    )


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


def platform_dispatch(d, *args, **kwargs):
    for name, f in d.items():
        if sys.platform.startswith(name):
            f(*args, **kwargs)
            break
    else:
        raise Exception('Platform not supported: {}'.format(sys.platform))


def install_python(*args, **kwargs):
    d = {
        'linux': install_python_linux,
        # 'darwin': install_python_darwin,
        # 'win': install_python_windows,
    }

    platform_dispatch(d, *args, **kwargs)


def get_virtualenv():
    url = (
        'https://raw.githubusercontent.com'
        '/pypa/virtualenv/16.2.0/virtualenv.py'
    )

    path = 'virtualenv.py'

    get_url(url=url, path=path)

    return path


def main():
    version = os.environ['TRAVIS_PYTHON_VERSION']
    install_python(version)

    virtualenv_py = get_virtualenv()

    env_path = '.venv'

    check_call(
        [
            'python{}'.format(version),
            virtualenv_py,
            env_path,
        ],
    )


main()
