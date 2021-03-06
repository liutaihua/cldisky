import os
import sys
import pkg_resources
import sys

def confecho(out=sys.stdout):
    config = pkg_resources.resource_string(__name__, 'skel/sample.conf')
    out.write(config)
    if not os.path.exists('/etc/cldisky.conf'):
        file = open('/etc/cldisky.conf','w')
        file.write(config)
        file.close()
