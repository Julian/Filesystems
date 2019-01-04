import logging
import os
import subprocess
import sys


logger = logging.getLogger(__name__)


cache_root = 'cache'
pyenv_root = os.path.join(cache_root, 'pyenv')


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

        pyenv.run('rehash')

        return pyenv

    def python_path(self, version):
        directory = os.path.join(self.root, 'shims')
        file_path = os.path.join(directory, python_name_from_version(version))
        if not os.path.exists(file_path):
            logger.info('Contents of {}'.format(directory))
            logger.info('\n'.join(os.listdir(directory)))

        return file_path

    def run(self, *args):
        env = dict(os.environ)
        env['PYENV_ROOT'] = self.root

        command = (os.path.join(self.root, 'bin', 'pyenv'),)
        command += args

        check_call(command, env=env)


def install_python_via_pyenv(version):
    pyenv = PyEnv.install(root=pyenv_root)
    pyenv.run('install', version)
    pyenv.run('global', version)

    return pyenv.python_path(version)


def platform_dispatch(d, *args, **kwargs):
    for name, f in d.items():
        if sys.platform.startswith(name):
            return f(*args, **kwargs)
    else:
        raise Exception('Platform not supported: {}'.format(sys.platform))


def install_python(*args, **kwargs):
    d = {
        'linux': install_python_via_pyenv,
        'darwin': install_python_via_pyenv,
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


class ForEval:
    def __init__(self):
        self.lines = []

    def add(self, *lines):
        self.lines.extend(lines)
        for line in lines:
            print(line)

    def for_log(self):
        return '\n'.join(self.lines)


def main():
    logger = logging.getLogger()
    log_path = os.path.splitext(os.path.basename(__file__))[0] + '.log'
    logger.addHandler(logging.FileHandler(log_path))
    logger.setLevel(logging.DEBUG)

    for_eval = ForEval()

    for_eval.add('cat {}'.format(log_path))

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

    python_path = os.path.dirname(python_path)
    if len(python_path) > 0:
        for_eval.add('export PATH={}:$PATH'.format(python_path))

    the_rest = '''
        export TRAVIS_PYTHON_VERSION={travis_python_version}
        source {env_path}/bin/activate
    '''.format(
        travis_python_version=python_name_from_version(version),
        env_path=env_path,
    )

    for_eval.add(*the_rest.splitlines())

    logger.info(for_eval.for_log())


main()
