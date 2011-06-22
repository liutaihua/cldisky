import os
import sys
import pkg_resources
import sys
from scaning import MyDaemon

def cldisky():
    if not sys.argv[1:]:
        print "commands: start|stop|restart"
        sys.exit(0)

    daemon = MyDaemon('/tmp/cldisky.pid')
    if sys.argv[1] == 'start':
        daemon.start()
    elif sys.argv[1] == 'stop':
        daemon.stop()
    elif sys.argv[1] == 'restart':
        daemon.stop()
        daemon.start()
    else:
        print "commands: start|stop|restart"
if __name__ == "__main__":
    confecho()
