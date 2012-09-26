#-*- coding: utf8 -*-
import logging
import random
from logging.handlers import RotatingFileHandler
import time


def initlog(logfile, maxlogsize=10, backupcount=4, format='%(message)s', level='DEBUG'):
    maxlogsize = int(maxlogsize)*1024*1024 #Bytes
    level = getattr(logging, level)

    handler = RotatingFileHandler(logfile,
                                  mode='a',
                                  maxBytes=maxlogsize,
                                  backupCount=backupcount)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

if __name__ == "__main__":
    logger = initlog('myapp.log', maxlogsize=1)
    for i in range(1000000):
        msg = ''.join(random.sample([chr(i) for i in range(48, 100)]*10, 50))
        logger.debug(msg)
