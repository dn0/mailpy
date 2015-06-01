#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

from mailpy import __version__

read = lambda fname: open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='mailpy',
    version=__version__,
    description='Mail API framework',
    long_description=read('README.rst'),
    author='Daniel Kontšek',
    author_email='daniel [at] kontsek.sk',
    url='https://github.com/dn0/mailpy/',
    license='BSD',
    packages=['mailpy'],
    platforms='any',
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Topic :: Communications :: Email',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
