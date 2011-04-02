# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
from distutils.core import setup
setup( name = 'cldisky',
       version = '1.0',
       description='My Blog Distribution Utilities',
       author='Liu Taihua',
       author_email='defage@gmail.com',
       url='http://www.fmcache.com',
    license='GPL',
    #package_dir = {'':'cldisky'},
    #packages = find_packages(os.path.join(here, 'cldisky')),
    packages=find_packages(),
    package_data={
        'cldisky': [
            'cldisky/*',
        ]
    },
    install_requires=[
        'paramiko',
    ],
    entry_points = {
        'console_scripts': [
            'cldisky = cldisky.scripts:cldisky',
            'cldisky_confecho = cldisky.scripts:confecho',
        ]
    },

)



