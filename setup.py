"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(

    name='acq400_hapi_beta',

    description='A python package for use with ACQ400 series D-TACQ modules.',

    url='https://github.com/seanalsop/acq400_hapi',

    classifiers=[

        'Development Status :: 4 - Beta',

        'Intended Audience :: Researchers/Developers',

        'Topic :: Software Development :: Build Tools',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',

    ],


    keywords='sample setuptools development',  # Optional

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required

    install_requires=['numpy'],

)