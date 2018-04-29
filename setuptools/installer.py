import glob
import os.path
import subprocess
import sys
import warnings
from distutils.errors import DistutilsError

import pkg_resources
from setuptools.wheel import Wheel

from .py31compat import TemporaryDirectory


def fetch_build_egg(req, eggs_dir, quiet=None,
                    index_url=None, find_links=None):
    """Fetch an egg needed for building"""
    if not isinstance(req, pkg_resources.Requirement):
        req = pkg_resources.Requirement.parse(req)
    eggs_dir = os.path.realpath(eggs_dir)
    environment = pkg_resources.Environment()
    for dist in pkg_resources.find_distributions(eggs_dir):
        if dist in req and environment.can_add(dist):
            return dist
    # Check pip is available.
    try:
        pkg_resources.get_distribution('pip')
    except pkg_resources.DistributionNotFound as e:
        raise DistutilsError(str(e))
    # Warn if wheel is not.
    try:
        pkg_resources.get_distribution('wheel')
    except pkg_resources.DistributionNotFound as e:
        warnings.warn("wheel is not installed.")
    with TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable, '-m', 'pip',
            '--disable-pip-version-check',
            'wheel', '--no-deps',
            '-w', tmpdir,
        ]
        if quiet is not None and quiet:
            cmd.append('--quiet')
        if index_url is not None:
            cmd.extend(('--index-url', index_url))
        if find_links is not None:
            for link in find_links:
                cmd.extend(('--find-links', link))
        # If requirement is a PEP 508 direct URL, directly pass
        # the URL to pip, as `req @ url` does not work on the
        # command line.
        if req.url:
            cmd.append(req.url)
        else:
            cmd.append(str(req))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise DistutilsError(str(e))
        wheel = Wheel(glob.glob(os.path.join(tmpdir, '*.whl'))[0])
        dist_location = os.path.join(eggs_dir, wheel.egg_name())
        wheel.install_as_egg(dist_location)
        dist_metadata = pkg_resources.PathMetadata(
            dist_location, os.path.join(dist_location, 'EGG-INFO'))
        dist = pkg_resources.Distribution.from_filename(
            dist_location, metadata=dist_metadata)
        return dist
