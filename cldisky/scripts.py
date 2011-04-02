import os
import sys
import pkg_resources
import sys

def confecho(out=sys.stdout):
    config = pkg_resources.resource_string(__name__, 'config.py')
    out.write(config)

def cldisk():
    os.system('/usr/bin/python /usr/lib/python2.6/site-packages/cldisk-1.0-py2.6.egg/cldisk/scaning.py start')

