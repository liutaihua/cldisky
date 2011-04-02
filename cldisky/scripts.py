import os
import sys
import pkg_resources
import sys
from scaning import *

def confecho(out=sys.stdout):
    config = pkg_resources.resource_string(__name__, 'config.py')
    out.write(config)

def cldisky_start():
    daemon = MyDaemon('/tmp/daemon.pid')
    daemon.start()

def cldisky_stop():
    daemon = MyDaemon('/tmp/daemon.pid')
    daemon.stop()


#if __name__ == "__main__":
#    cldisky()
