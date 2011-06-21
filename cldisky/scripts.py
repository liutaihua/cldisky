import os
import sys
import pkg_resources
import sys
from scaning import MyDaemon

def cldisky_start():
    daemon = MyDaemon('/var/run/cldisky.pid')
    daemon.start()

def cldisky_stop():
    daemon = MyDaemon('/var/run/cldisky.pid')
    daemon.stop()


if __name__ == "__main__":
    confecho()
