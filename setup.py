#!/usr/bin/env python
"""
Distutils setup file, used to install or test 'setuptools'
"""

import os
import sys

import setuptools

here = os.path.dirname(__file__)


def require_metadata():
    "Prevent improper installs without necessary metadata. See #659"
    egg_info_dir = os.path.join(here, 'setuptools.egg-info')
    if not os.path.exists(egg_info_dir):
        msg = (
            "Cannot build setuptools without metadata. "
            "Run `bootstrap.py`."
        )
        raise RuntimeError(msg)


def read_commands():
    command_ns = {}
    cmd_module_path = 'setuptools/command/__init__.py'
    init_path = os.path.join(here, cmd_module_path)
    with open(init_path) as init_file:
        exec(init_file.read(), command_ns)
    return command_ns['__all__']


package_data = dict(
    setuptools=['script (dev).tmpl', 'script.tmpl', 'site-patch.py'],
)

force_windows_specific_files = (
    os.environ.get("SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES", "1").lower()
    not in ("", "0", "false", "no")
)

include_windows_files = (
    sys.platform == 'win32' or
    os.name == 'java' and os._name == 'nt' or
    force_windows_specific_files
)

if include_windows_files:
    package_data.setdefault('setuptools', []).extend(['*.exe'])
    package_data.setdefault('setuptools.command', []).extend(['*.xml'])

needs_wheel = set(['release', 'bdist_wheel']).intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []


setup_params = dict(
    src_root=None,
    package_data=package_data,
    entry_points={
        "distutils.commands": [
            "%(cmd)s = setuptools.command.%(cmd)s:%(cmd)s" % locals()
            for cmd in read_commands()
        ],
        "distutils.setup_keywords": [
            "eager_resources        = setuptools.dist:assert_string_list",
            "namespace_packages     = setuptools.dist:check_nsp",
            "extras_require         = setuptools.dist:check_extras",
            "install_requires       = setuptools.dist:check_requirements",
            "tests_require          = setuptools.dist:check_requirements",
            "setup_requires         = setuptools.dist:check_requirements",
            "python_requires        = setuptools.dist:check_specifier",
            "entry_points           = setuptools.dist:check_entry_points",
            "test_suite             = setuptools.dist:check_test_suite",
            "zip_safe               = setuptools.dist:assert_bool",
            "package_data           = setuptools.dist:check_package_data",
            "exclude_package_data   = setuptools.dist:check_package_data",
            "include_package_data   = setuptools.dist:assert_bool",
            "packages               = setuptools.dist:check_packages",
            "dependency_links       = setuptools.dist:assert_string_list",
            "test_loader            = setuptools.dist:check_importable",
            "test_runner            = setuptools.dist:check_importable",
            "use_2to3               = setuptools.dist:assert_bool",
            "convert_2to3_doctests  = setuptools.dist:assert_string_list",
            "use_2to3_fixers        = setuptools.dist:assert_string_list",
            "use_2to3_exclude_fixers = setuptools.dist:assert_string_list",
        ],
        "egg_info.writers": [
            "PKG-INFO = setuptools.command.egg_info:write_pkg_info",
            "requires.txt = setuptools.command.egg_info:write_requirements",
            "entry_points.txt = setuptools.command.egg_info:write_entries",
            "eager_resources.txt = setuptools.command.egg_info:overwrite_arg",
            (
                "namespace_packages.txt = "
                "setuptools.command.egg_info:overwrite_arg"
            ),
            "top_level.txt = setuptools.command.egg_info:write_toplevel_names",
            "depends.txt = setuptools.command.egg_info:warn_depends_obsolete",
            "dependency_links.txt = setuptools.command.egg_info:overwrite_arg",
        ],
        "setuptools.installation":
            ['eggsecutable = setuptools.command.easy_install:bootstrap'],
    },
    setup_requires=[
    ] + wheel,
)

if __name__ == '__main__':
    # allow setup.py to run from another directory
    here and os.chdir(here)
    require_metadata()
    dist = setuptools.setup(**setup_params)
