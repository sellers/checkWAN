#!/usr/bin/env python
# installer via setup.py install
#

from distutils.core import setup

setup(name='Distutils',
    version='1.0',
    description='Python Dist Utils',
    author='Sellers',
    author_email='cgseller@gmail.com',
    url='http://www.python.org/sigs/distutils-sig',
    entry_points={
            'console_scripts': ['checkWAN = checkWAN.check_wan.py:main', ]
            }
)
