# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
from distutils.core import setup
dist = setup( name = 'cldisky',
       version = '1.0',
       description='My Blog Distribution Utilities',
       author='Liu Taihua',
       author_email='defage@gmail.com',
       url='http://www.fmcache.com',
    license='GPL',
    packages=['','skel','cldisky'],
    package_dir = {'':'cldisky','cldisky':'cldisky','skel':'cldisky/skel'},
    #packages = find_packages(os.path.join('cldisky')),
    scripts=['cldisky/readconf.py','cldisky/skel/sample.conf'],
    package_data={
        'cldisky': [
            'cldisky/*',
            'skel/*',
        ]
    },
    install_requires=[
        'paramiko',
    ],
    #requires = ['paramiko'],
    entry_points = {
        'console_scripts': [
            'cldisky = cldisky.scripts:cldisky',
            'cldisky_confecho = cldisky.confecho:main',
        ]
    },

)


