#!/usr/bin/env python
# installer via setup.py install
# License: CreativeCommons 2015
'''
setup
'''

from setuptools import setup

setup(name='checkWAN',
      version='0.2.0',
      description='Python Dist Utils for CHECKWAN',
      packages=['checkwan'],
      author='Sellers',
      author_email='cgseller@gmail.com',
      entry_points={
          'console_scripts': ['checkWAN=checkwan.check_wan:main', ]
          },
      package_data={'checkwan' : ['conf/check_wan.cfg']
                   },
      include_package_data=True,
     )
