#! /usr/bin/python

import os
import sys
import logging

logging.raiseExceptions = False

__loggingInit = False
__ainstLogger = None
__userLogger = None

class CompositeLogger:
    def __init__(self, loggers):
        self._loggers = loggers

    def log(self, level, msg):
        if not self._loggers:
            return
        for logger in self._loggers:
            logger.log(level, msg)

    def flush(self):
        if not self._loggers:
            return False
        for logger in self._loggers:
            for handler in logger.handlers:
                handler.flush()
        return True

def __convertLevel(level):
    if level == 'debug':
        return logging.DEBUG
    elif level == 'info':
        return logging.INFO
    elif level == 'warning':
        return logging.WARNING
    elif level == 'error':
        return logging.ERROR
    elif level == 'critical':
        return logging.CRITICAL
    return None

def init(ainstLogFile, ainstLogLevel='debug', userLogLevel='info'):
    global __loggingInit
    global __ainstLogger
    global __userLogger
    if __loggingInit:
        return True
    preUmask = os.umask(0)
    try:
        userLogLevel = __convertLevel(userLogLevel)
        if userLogLevel is None:
            userLogLevel = logging.INFO
        consoleFormatter = logging.Formatter('%(message)s')
        userHandler = logging.StreamHandler(sys.stdout)
        userHandler.setFormatter(consoleFormatter)
        userHandler.setLevel(userLogLevel)
        __userLogger = logging.getLogger('user')
        __userLogger.addHandler(userHandler)
        __userLogger.setLevel(userLogLevel)
        __userLogger.propagate = 0
    
        ainstLogLevel = __convertLevel(ainstLogLevel)
        if ainstLogLevel is None:
            ainstLogLevel = logging.DEBUG
        formatterStr = '[%(asctime)s %(levelname)s] %(message)s'
        fileFormatter = logging.Formatter(formatterStr)
        ainstHandler = logging.FileHandler(ainstLogFile)
        ainstHandler.setFormatter(fileFormatter)
        ainstHandler.setLevel(ainstLogLevel)
        __ainstLogger = logging.getLogger('ainst')
        __ainstLogger.addHandler(ainstHandler)
        __ainstLogger.setLevel(ainstLogLevel)
        __ainstLogger.propagate = 0

        __loggingInit = True
        os.umask(preUmask)
    except Exception,e:
        print 'Init ainst logging failed: %s' % str(e)
        os.umask(preUmask)
        return False
    return True

def close():
    global __loggingInit
    global __ainstLogger
    global __userLogger
    __loggingInit = False
    __ainstLogger = None
    __userLogger = None

def getLogger(name):
    if not __loggingInit:
        return None
    if name == 'all':
        return CompositeLogger([__ainstLogger, __userLogger])
    elif name == 'ainst':
        return CompositeLogger([__ainstLogger])
    elif name == 'user':
        return CompositeLogger([__userLogger])
    return None

if __name__ == '__main__':
    path = '/home/xiaoming.zhang/x'
    if not init(path):
        import sys
        sys.exit(1)
    logger = getLogger('ainst')
    logger.error('b')
    logger = getLogger('user')
    logger.error('b')
 
