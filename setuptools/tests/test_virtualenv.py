from contextlib import contextmanager
import glob
import os
import sys

import pytest
from pytest import yield_fixture
from pytest_fixture_config import yield_requires_config

import pytest_virtualenv

import filelock

from setuptools.extern import six

from .textwrap import DALS
from .test_easy_install import make_nspkg_sdist


@yield_requires_config(pytest_virtualenv.CONFIG, ['virtualenv_executable'])
@yield_fixture(scope='function')
def bare_virtualenv():
    """ Bare virtualenv (no pip/setuptools/wheel).
    """
    with pytest_virtualenv.VirtualEnv(args=(
        '--no-wheel',
        '--no-pip',
        '--no-setuptools',
    )) as venv:
        yield venv


SOURCE_DIR = os.path.join(os.path.dirname(__file__), '../..')
SOURCE_LOCK = os.path.join(SOURCE_DIR, '.lock')

@contextmanager
def locked_source_dir():
    with filelock.FileLock(SOURCE_LOCK):
        yield


def test_clean_env_install(bare_virtualenv):
    """
    Check setuptools can be installed in a clean environment.
    """
    virtualenv = bare_virtualenv
    with locked_source_dir():
        virtualenv.run((virtualenv.python, 'setup.py', 'install'), cd=SOURCE_DIR)


def _get_pip_versions():
    # This fixture will attempt to detect if tests are being run without
    # network connectivity and if so skip some tests

    network = True
    if not os.environ.get('NETWORK_REQUIRED', False):  # pragma: nocover
        try:
            from urllib.request import urlopen
            from urllib.error import URLError
        except ImportError:
            from urllib2 import urlopen, URLError # Python 2.7 compat

        try:
            urlopen('https://pypi.org', timeout=1)
        except URLError:
            # No network, disable most of these tests
            network = False

    network_versions = [
        'pip==9.0.3',
        'pip==10.0.1',
        'pip==18.1',
        'pip==19.1.1',
    ]

    # pip>19.1.1 dropped support for 3.4.
    if not six.PY34:
        network_versions.extend((
            'pip==19.2.2',
            'https://github.com/pypa/pip/archive/master.zip',
        ))

    versions = [None] + [
        pytest.param(v, **({} if network else {'marks': pytest.mark.skip}))
        for v in network_versions
    ]

    return versions


@yield_requires_config(pytest_virtualenv.CONFIG, ['virtualenv_executable'])
@yield_fixture(scope='function')
def pip_only_virtualenv():
    """ Bare virtualenv (no pip/setuptools/wheel).
    """
    with pytest_virtualenv.VirtualEnv(args=(
        '--no-wheel',
        '--no-setuptools',
    )) as venv:
        yield venv


@pytest.mark.parametrize('pip_version', _get_pip_versions())
def test_pip_upgrade_from_source(pip_version, pip_only_virtualenv):
    """
    Check pip can upgrade setuptools from source.
    """
    virtualenv = pip_only_virtualenv
    # Install/update wheel/pip.
    to_update = ['wheel']
    if pip_version is not None:
        to_update.append(pip_version)
    virtualenv.run([virtualenv.python, '-m', 'pip', '--disable-pip-version-check',
                    'install', '--upgrade'] + to_update)
    dist_dir = virtualenv.workspace
    with locked_source_dir():
        # Generate source distribution / wheel.
        virtualenv.run((virtualenv.python, 'setup.py', '-q',
                        'sdist', '-d', dist_dir,
                        'bdist_wheel', '-d', dist_dir,
                       ), cd=SOURCE_DIR)
    sdist = glob.glob(os.path.join(dist_dir, '*.zip'))[0]
    wheel = glob.glob(os.path.join(dist_dir, '*.whl'))[0]
    # Then update from wheel.
    virtualenv.run((virtualenv.python, '-m', 'pip', '--disable-pip-version-check',
                    'install', wheel))
    # And finally try to upgrade from source.
    virtualenv.run((virtualenv.python, '-m', 'pip', '--disable-pip-version-check',
                    '--no-cache-dir', 'install', '--upgrade', sdist))


def test_test_command_install_requirements(virtualenv, tmpdir):
    """
    Check the test command will install all required dependencies.
    """
    virtualenv.run((virtualenv.python, '-m', 'pip', '--disable-pip-version-check',
                    'install', '--upgrade', 'pip'))
    with locked_source_dir():
        virtualenv.run((
            virtualenv.python, '-m', 'pip', '--disable-pip-version-check',
            'install', '--no-use-pep517', '-e', SOURCE_DIR,
        ))

    def sdist(distname, version):
        dist_path = tmpdir.join('%s-%s.tar.gz' % (distname, version))
        make_nspkg_sdist(str(dist_path), distname, version)
        return dist_path
    dependency_links = [
        str(dist_path)
        for dist_path in (
            sdist('foobar', '2.4'),
            sdist('bits', '4.2'),
            sdist('bobs', '6.0'),
            sdist('pieces', '0.6'),
        )
    ]
    with tmpdir.join('setup.py').open('w') as fp:
        fp.write(DALS(
            '''
            from setuptools import setup

            setup(
                dependency_links={dependency_links!r},
                install_requires=[
                    'barbazquux1; sys_platform in ""',
                    'foobar==2.4',
                ],
                setup_requires='bits==4.2',
                tests_require="""
                    bobs==6.0
                """,
                extras_require={{
                    'test': ['barbazquux2'],
                    ':"" in sys_platform': 'pieces==0.6',
                    ':python_version > "1"': """
                        pieces
                        foobar
                    """,
                }}
            )
            '''.format(dependency_links=dependency_links)))
    with tmpdir.join('test.py').open('w') as fp:
        fp.write(DALS(
            '''
            import foobar
            import bits
            import bobs
            import pieces

            open('success', 'w').close()
            '''))
    # Run test command for test package.
    virtualenv.run((virtualenv.python, 'setup.py', 'test', '-s', 'test'),
                   cd=str(tmpdir))
    assert tmpdir.join('success').check()


def test_no_missing_dependencies(bare_virtualenv):
    """
    Quick and dirty test to ensure all external dependencies are vendored.
    """
    virtualenv = bare_virtualenv
    for command in ('upload',):  # sorted(distutils.command.__all__):
        with locked_source_dir():
            virtualenv.run((virtualenv.python, 'setup.py', command, '-h'),
                           cd=SOURCE_DIR)
