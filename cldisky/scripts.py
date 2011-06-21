import os
import sys
import pkg_resources
import sys
from scaning import MyDaemon

def cldisky_start():
    if not os.path.exists('/etc/cldisky.conf'):
        os.system('cldisky_confecho')
    daemon = MyDaemon('/var/run/cldisky.pid')
    daemon.start()

def cldisky_stop():
    daemon = MyDaemon('/var/run/cldisky.pid')
    daemon.stop()


if __name__ == "__main__":
    confecho()
