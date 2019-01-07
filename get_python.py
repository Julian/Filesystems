import logging
import os
import subprocess
import sys
import textwrap


logger = logging.getLogger(__name__)


cache_root = os.path.join(os.getcwd(), 'cache')
pyenv_root = os.path.join(cache_root, 'pyenv')
windows_python_root = os.path.join(cache_root, 'python')


def check_call(args, *pargs, **kwargs):
    args = list(args)
    logger.info('Launching: ')
    for arg in args:
        logger.info('    {}'.format(arg))

    process = subprocess.Popen(
        args,
        *pargs,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        **kwargs
    )

    stdout, _ = process.communicate()

    for line in stdout.splitlines():
        logger.info(line)


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
    is_pypy = version.startswith('pypy')

    version_segments = 1 if is_pypy else 2
    split_version = version.replace('-', '.').split('.')
    tweaked_version = '.'.join(split_version[:version_segments])

    if is_pypy:
        return {
            'pypy2': 'pypy',
        }.get(tweaked_version, tweaked_version)

    return 'python{}'.format(tweaked_version)


def install_python_like_travis(version):
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


class PyEnv:
    def __init__(self, root):
        self.root = root

    @classmethod
    def install(cls, root):
        root_parent = os.path.dirname(root)
        try:
            os.makedirs(root_parent)
        except os.error:
             pass

        archive = 'pyenv_archive.zip'

        get_url(
            url='https://github.com/pyenv/pyenv/archive/master.zip',
            path=archive,
        )

        check_call(['unzip', '-d', root_parent, archive])
        os.rename(
            os.path.join(root_parent, 'pyenv-master'),
            pyenv_root,
        )

        pyenv = cls(root=root)

        return pyenv

    def python_path(self, version):
        return os.path.join(self.root, 'versions', version, 'bin', 'python')

    def run(self, *args):
        env = dict(os.environ)
        env['PYENV_ROOT'] = self.root

        command = (os.path.join(self.root, 'bin', 'pyenv'),)
        command += args

        check_call(command, env=env)


def install_python_via_pyenv(version):
    pyenv = PyEnv.install(root=pyenv_root)
    pyenv.run('install', version)

    return pyenv.python_path(version)


def windows_cpython_installer_url(version):
    split_version = [int(x) for x in version.split('.')]
    dash_or_dot = '.' if split_version < [3, 5] else '-'
    msi_or_exe = 'msi' if split_version < [3, 5] else 'exe'

    return (
        'https://www.python.org/ftp/python/{version}'
        '/python-{version}.{msi_or_exe}'.format(
        # '/python-{version}{dash_or_dot}amd64.msi'.format(
            version=version,
            dash_or_dot=dash_or_dot,
            msi_or_exe=msi_or_exe,
        )
    )


def windows_cpython_install(url):
    installer = os.path.join(os.getcwd(), 'python.exe')

    get_url(url=url, path=installer)

    check_call(
        [
            installer,
            '/quiet',
            'TargetDir={}'.format(windows_python_root),
        ],
    )

    return os.path.join(windows_python_root, 'python.exe')


def windows_pypy_installer_url(version):
    url = 'https://bitbucket.org/pypy/pypy/downloads/{version}-win32.zip'
    url = url.format(version=version)
    return url


def windows_pypy_install(version, url):
    archive = os.path.join(os.getcwd(), 'python.zip')

    get_url(url=url, path=archive)

    check_call(
        [
            'unzip',
            archive,
        ],
    )

    os.rename(
        '{version}-win32'.format(version=version),
        windows_python_root,
    )

    return os.path.join(windows_python_root, 'pypy.exe')


def install_python_windows(version):
    if version.startswith('pypy'):
        url = windows_pypy_installer_url(version)
        return windows_pypy_install(url)

    url = windows_cpython_installer_url(version)
    return windows_cpython_install(version, url)


def get_platform():
    for name in ('linux', 'darwin', 'win'):
        if sys.platform.startswith(name):
            return name
    else:
        raise Exception('Platform not supported: {}'.format(sys.platform))


def platform_dispatch(d, *args, **kwargs):
    return d[the_platform](*args, **kwargs)


def install_python(*args, **kwargs):
    d = {
        'linux': install_python_via_pyenv,
        'darwin': install_python_via_pyenv,
        'win': install_python_windows,
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


def create_sh_content(version, env_path, python_path):
    set_path = None
    if len(python_path) > 0:
        set_path = 'export PATH={}:$PATH\n'.format(python_path)

    bin_or_scripts = 'scripts' if the_platform == 'win' else 'bin'

    content = textwrap.dedent('''\
    export TRAVIS_PYTHON_VERSION={travis_python_version}
    source {env_path}/{bin_or_scripts}/activate
    {set_path}
    ''').format(
        travis_python_version=python_name_from_version(version),
        env_path=env_path,
        bin_or_scripts=bin_or_scripts,
        set_path=set_path if set_path is not None else '',
    )

    return content.strip() + '\n'


def main():
    logger = logging.getLogger()
    log_path = os.path.splitext(os.path.basename(__file__))[0] + '.log'
    logger.addHandler(logging.FileHandler(log_path))
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    version = os.environ['PYTHON']
    python_path = install_python(version)

    virtualenv_path = get_virtualenv('16.2.0')

    env_path = '.venv'

    env = dict(os.environ)
    env['PYTHONPATH'] = virtualenv_path

    python_dir = os.path.dirname(python_path)
    logger.info('Content of: {}'.format(python_dir))
    for name in os.listdir(python_dir):
        logger.info('    {}'.format(name))

    check_call(
        [
            python_path,
            '-m', 'virtualenv',
            env_path,
        ],
        env=env,
    )

    python_path = os.path.dirname(python_path)

    script_content = create_sh_content(
        version=version,
        env_path=env_path,
        python_path=python_path,
    )

    logger.info('   script content:')
    logger.info(script_content)

    with open('get_python.sh', 'w') as f:
        f.write(script_content)


the_platform = get_platform()
main()
