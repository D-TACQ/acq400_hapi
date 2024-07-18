"""Setuptools-based installation script for acq400_hapi.

See:

https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
import git

# find the latest Git tag of the current checkout, reduce it to X.Y.Z format, should
# work on all platforms:
repo = git.Repo()
version = repo.git.describe('--tags')
version = version.split('-')[0].lstrip('v')

setup(
    name='acq400_hapi',
    version=version,
    description='A Python package for connection ACQ400 series D-TACQ products.',
    url='https://github.com/D-TACQ/acq400_hapi',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='D-TACQ',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['future'],
)
