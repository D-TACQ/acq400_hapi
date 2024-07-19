"""Setuptools-based installation script for acq400_hapi.

See:

https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from acq400_hapi import __version__


setup(
    name='acq400_hapi',
    version=__version__,
    description='A Python package for connection ACQ400 series D-TACQ products.',
    url='https://github.com/D-TACQ/acq400_hapi',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='D-TACQ',
)
