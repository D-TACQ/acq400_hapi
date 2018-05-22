"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

from subprocess import Popen, PIPE

p = Popen("./package/git-get-release", stdout=PIPE, stderr=PIPE)
(GITVERSION, ERR) = p.communicate()

if ERR:
    print(ERR)
    raise SystemExit
else:
    GITVERSION=GITVERSION.rstrip()

setup(

    name='acq400_hapi',

    version=GITVERSION,

    description='A python package for connection ACQ400 series D-TACQ products.',

    url='https://github.com/D-TACQ/acq400_hapi',

    classifiers=[

        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',

        'Topic :: Software Development :: Build Tools',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',

    ],


    keywords='D-TACQ',  

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  

    install_requires=['numpy', 'future'],

)
