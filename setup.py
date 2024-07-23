"""Setuptools-based installation script for acq400_hapi.

See:

https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup
import os
import subprocess

MODULE_DIR = os.path.dirname(__file__)

def get_version():
    proc = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE)
    if proc.returncode == 0:
        return proc.stdout.decode().strip().replace('-', '+', 1)
    return "0.0.0+nogit"

setup(
    name='acq400_hapi',
    version= get_version(),
    description='A Python package for connection ACQ400 series D-TACQ products.',
    url='https://github.com/D-TACQ/acq400_hapi',
    packages=["acq400_hapi"],
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
