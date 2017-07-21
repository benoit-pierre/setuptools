import glob
import os
import sys

import pytest
from pytest import yield_fixture
from pytest_fixture_config import yield_requires_config

import pytest_virtualenv

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

def test_clean_env_install(bare_virtualenv):
    """
    Check setuptools can be installed in a clean environment.
    """
    bare_virtualenv.run(' && '.join((
        'cd {source}',
        'python setup.py install',
    )).format(source=SOURCE_DIR))

def test_pip_upgrade_from_source(virtualenv):
    """
    Check pip can upgrade setuptools from source.
    """
    dist_dir = virtualenv.workspace
    # Generate source distribution / wheel.
    virtualenv.run(' && '.join((
        'cd {source}',
        'python setup.py -q sdist -d {dist}',
        'python setup.py -q bdist_wheel -d {dist}',
    )).format(source=SOURCE_DIR, dist=dist_dir))
    sdist = glob.glob(os.path.join(dist_dir, '*.zip'))[0]
    wheel = glob.glob(os.path.join(dist_dir, '*.whl'))[0]
    # Then update from wheel.
    virtualenv.run('pip install ' + wheel)
    # And finally try to upgrade from source.
    virtualenv.run('pip install --no-cache-dir --upgrade ' + sdist)

@pytest.mark.xfail(sys.version_info >= (3, 7), reason='Fail on nightly')
def test_dist_fetch_build_eggs(bare_virtualenv, tmpdir):
    """
    Check `Distribution.fetch_build_eggs` work as expected.
    """
    bare_virtualenv.run(' && '.join((
        'cd {source}',
        'python setup.py develop',
    )).format(source=SOURCE_DIR))
    reqs = 'pytest pytest-runner'.split()
    with tmpdir.join('fetch_eggs.py').open('w') as fp:
        fp.write(DALS(
            '''
            from setuptools import Distribution
            dist = Distribution()
            dist.fetch_build_eggs({reqs})
            '''
        ).format(reqs=reqs))
    with tmpdir.join('check_eggs.py').open('w') as fp:
        fp.write(DALS(
            '''
            from setuptools import Distribution
            from pkg_resources import find_distributions
            reqs = set({reqs})
            egg_cache_dir = Distribution().get_egg_cache_dir()
            installed = set(dist.project_name for dist in find_distributions(egg_cache_dir))
            assert reqs & installed == reqs
            ''').format(reqs=reqs))
    bare_virtualenv.run(' && '.join((
        'cd {tmpdir}',
        'python fetch_eggs.py',
        'python check_eggs.py',
    )).format(tmpdir=tmpdir))

def test_test_command_install_requirements(bare_virtualenv, tmpdir):
    """
    Check the test command will install all required dependencies.
    """
    bare_virtualenv.run(' && '.join((
        'cd {source}',
        'python setup.py develop',
    )).format(source=SOURCE_DIR))
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
                setup_requires=['bits==4.2'],
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
    bare_virtualenv.run(' && '.join((
        'cd {tmpdir}',
        'python setup.py test -s test',
    )).format(tmpdir=tmpdir))
    assert tmpdir.join('success').check()
