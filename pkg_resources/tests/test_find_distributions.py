import subprocess
import sys

import pytest
import pkg_resources

SETUP_TEMPLATE = """
import setuptools
setuptools.setup(
    name="my-test-package",
    version="1.0",
    zip_safe=True,
)
""".lstrip()


class TestFindDistributions:

    @pytest.fixture
    def target_dir(self, tmpdir):
        target_dir = tmpdir.mkdir('target')
        # place a .egg named directory in the target that is not an egg:
        target_dir.mkdir('not.an.egg')
        return str(target_dir)

    @pytest.fixture
    def project_dir(self, tmpdir):
        project_dir = tmpdir.mkdir('my-test-package')
        (project_dir / "setup.py").write(SETUP_TEMPLATE)
        return str(project_dir)

    def test_non_egg_dir_named_egg(self, target_dir):
        dists = pkg_resources.find_distributions(target_dir)
        assert not list(dists)
