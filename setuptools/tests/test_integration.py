"""Run some integration tests.

Try to install a few packages.
"""

import os
import sys
import re
import subprocess
import functools
import tarfile
import zipfile

import pytest


build_deps = ['appdirs', 'packaging',
              pytest.param('pyparsing', marks=pytest.mark.skip(
                  reason="Project imports setuptools unconditionally"
              )),
              'six']


@pytest.mark.parametrize("build_dep", build_deps)
@pytest.mark.skipif(
    sys.version_info < (3, 6), reason='run only on late versions')
def test_build_deps_on_distutils(request, tmpdir_factory, build_dep):
    """
    All setuptools build dependencies must build without
    setuptools.
    """
    build_target = tmpdir_factory.mktemp('source')
    build_dir = download_and_extract(request, build_dep, build_target)
    install_target = tmpdir_factory.mktemp('target')
    output = install(build_dir, install_target)
    for line in output.splitlines():
        match = re.search('Unknown distribution option: (.*)', line)
        allowed_unknowns = [
            'test_suite',
            'tests_require',
            'python_requires',
            'install_requires',
        ]
        assert not match or match.group(1).strip('"\'') in allowed_unknowns


def install(pkg_dir, install_dir):
    with open(os.path.join(pkg_dir, 'setuptools.py'), 'w') as breaker:
        breaker.write('raise ImportError()')
    cmd = [sys.executable, 'setup.py', 'install', '--prefix', str(install_dir)]
    env = dict(os.environ, PYTHONPATH=str(pkg_dir))
    output = subprocess.check_output(
        cmd, cwd=pkg_dir, env=env, stderr=subprocess.STDOUT)
    return output.decode('utf-8')


def download_and_extract(request, req, target):
    cmd = [
        sys.executable, '-m', 'pip', 'download', '--no-deps',
        '--no-binary', ':all:', req,
    ]
    output = subprocess.check_output(cmd, encoding='utf-8')
    filename = re.search('Saved (.*)', output).group(1)
    request.addfinalizer(functools.partial(os.remove, filename))
    opener = zipfile.ZipFile if filename.endswith('.zip') else tarfile.open
    with opener(filename) as archive:
        archive.extractall(target)
    return os.path.join(target, os.listdir(target)[0])
