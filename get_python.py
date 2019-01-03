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
            '-L',
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

    return 'python{}'.format(version)


def install_python_darwin(version):
    # TODO: get the latest, not the earliest
    pyenv_version = os.environ['PYTHON{}'.format(version.replace('.', '_'))]

    check_call(['pyenv', 'install', pyenv_version])
    check_call(['pyenv', 'global', pyenv_version])

    return os.path.join(
        os.path.expanduser('~'),
        '.pyenv',
        'shims',
        'python{}'.format(version),
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
    version = os.environ['TRAVIS_PYTHON_VERSION']
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