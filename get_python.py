import logging
import os
import posixpath
import subprocess
import sys
import textwrap


logger = logging.getLogger(__name__)


cache_root = os.path.join(os.getcwd(), 'cache')
pyenv_root = os.path.join(cache_root, 'pyenv')
windows_python_root = os.path.join(cache_root, 'python')


def get_platform():
    for name in ('linux', 'darwin', 'win'):
        if sys.platform.startswith(name):
            return name
    else:
        raise Exception('Platform not supported: {}'.format(sys.platform))


the_platform = get_platform()


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


def install_python_via_pyenv_darwin(version):
    check_call(
        [
            'sudo',
            'installer',
            '-pkg',
            '/Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg',
            '-target',
            '/',
        ],
    )

    return install_python_via_pyenv(version)


def windows_cpython_installer_url(version):
    split_version = [int(x) for x in version.split('.')]
    dash_or_dot = '.' if split_version < [3, 5] else '-'
    msi_or_exe = 'msi' if split_version < [3, 5] else 'exe'

    return (
        'https://www.python.org/ftp/python/{version}'
        # '/python-{version}.{msi_or_exe}'.format(
        '/python-{version}{dash_or_dot}amd64.{msi_or_exe}'.format(
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


def windows_pypy_file_version(version):
    start, _, rest = version.partition('.')
    _, _, end = version.partition('-')
    return start + '-v' + end


def windows_pypy_installer_url(version):
    version = windows_pypy_file_version(version)
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

    os.makedirs(os.path.dirname(windows_python_root))

    file_version = windows_pypy_file_version(version)
    os.rename(
        '{version}-win32'.format(version=file_version),
        windows_python_root,
    )

    v = '' if version[len('pypy')] == '2' else '3'

    logger.info('   --- windows_pypy_install()')
    logger.info('   --- {!r}'.format(version))
    logger.info('   --- {!r}'.format(version[len('pypy')]))
    logger.info('   --- {!r}'.format(v))

    return os.path.join(windows_python_root, 'pypy{v}.exe'.format(v=v))


def install_python_windows(version):
    if version.startswith('pypy'):
        url = windows_pypy_installer_url(version)
        return windows_pypy_install(version, url)

    redist_urls = {}

    if version.split('.')[:2] == [2, 7]:
        redist_urls[32] = (
             'https://download.microsoft.com'
             '/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE'
             '/vcredist_x86.exe'
        )
        redist_urls[64] = (
             'https://download.microsoft.com'
             '/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE'
             '/vcredist_x64.exe'
        )
    elif version.split('.')[:2] == [3, 4]:
        redist_urls[32] = (
            'https://download.microsoft.com'
            '/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC'
            '/vcredist_x86.exe'
        )
        redist_urls[64] = (
            'https://download.microsoft.com'
            '/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC'
            '/vcredist_x64.exe'
        )

    bitness = 64
    redist_url = redist_urls.get(bitness)
    if redist_url is not None:
        redist_path = 'redist.exe'
        get_url(url=redist_url, path=redist_path)
        check_call([redist_path])

    url = windows_cpython_installer_url(version)
    return windows_cpython_install(url)


def platform_dispatch(d, *args, **kwargs):
    return d[the_platform](*args, **kwargs)


def install_python(*args, **kwargs):
    d = {
        'linux': install_python_via_pyenv,
        'darwin': install_python_via_pyenv_darwin,
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

    bin_or_scripts = (
        'Scripts'
        if the_platform == 'win' and not version.startswith('pypy')
        else 'bin'
    )

    logger.info('    ---- dir checks')

    activate_path = env_path
    logger.info('         ---- {}'.format(activate_path))
    logger.info(os.listdir(activate_path))

    activate_path = posixpath.join(activate_path, bin_or_scripts)
    logger.info('         ---- {}'.format(activate_path))
    logger.info(os.listdir(activate_path))

    activate_path = posixpath.join(activate_path, 'activate')

    content = textwrap.dedent('''\
    export TRAVIS_PYTHON_VERSION={travis_python_version}
    source {activate_path}
    {set_path}
    ''').format(
        travis_python_version=python_name_from_version(version),
        activate_path=activate_path,
        bin_or_scripts=bin_or_scripts,
        set_path=set_path if set_path is not None else '',
    )

    return content.strip() + '\n'


def main(sh_name):
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

    with open(sh_name, 'w') as f:
        f.write(script_content)


main(sh_name='get_python.sh')
