"""
Compatibility Support for Python 2.7 and earlier
"""

import platform

from setuptools.extern import six


linux_py2_ascii = (
    platform.system() == 'Linux' and
    six.PY2
)

rmtree_safe = str if linux_py2_ascii else lambda x: x
"""Workaround for http://bugs.python.org/issue24672"""
