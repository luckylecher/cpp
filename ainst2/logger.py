#! /usr/bin/python

import sys
import os
import inspect
import logging
import ainst_logging

class Log:
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    
    ALL_LOGGER = 'all'
    USER_LOGGER = 'user'
    AINST_LOGGER = 'ainst'

    @staticmethod
    def cout(level, content, logger=ALL_LOGGER):
        loggerObj = ainst_logging.getLogger(logger)
        if not loggerObj:
            return None
        loggerObj.log(level, content)

    @staticmethod
    def coutLabel(level, label, logger=ALL_LOGGER):
        content = Log._getLableLine(label)
        loggerObj = ainst_logging.getLogger(logger)
        if not loggerObj:
            return None
        loggerObj.log(level, content)
        
    @staticmethod
    def coutValue(level, key, value, logger=ALL_LOGGER):
        content = Log._getValueLine(key, value)
        loggerObj = ainst_logging.getLogger(logger)
        if not loggerObj:
            return None
        loggerObj.log(level, content)

    @staticmethod
    def coutValueList(level, keyValueList, logger=ALL_LOGGER):
        content = Log._getValueLines(keyValueList)
        loggerObj = ainst_logging.getLogger(logger)
        if not loggerObj:
            return None
        loggerObj.log(level, content)
        
    @staticmethod
    def coutConfirm():
        userInput = raw_input('Continue? [y/n]')
        if userInput == 'y':
            return True
        return False

    @staticmethod
    def flush(logger=ALL_LOGGER):
        loggerObj = ainst_logging.getLogger(logger)
        if not loggerObj:
            return False
        return loggerObj.flush()


    @staticmethod
    def _getLableLine(label, indent=100, fillChar='#'):
        if len(label) > indent:
            return None
        length = (indent - len(label)) / 2 - 1
        content = fillChar * length + ' ' + label + ' ' + fillChar * length
        if len(content) < indent:
            content = content + fillChar * (indent - len(content))
        elif len(content) > indent:
            content = content[0:indent]
        return content

    @staticmethod
    def _getValueLine(key, value, indent=100):
        return key.ljust(indent - len(value)) + value

    @staticmethod
    def _getValueLines(keyValueList, indent=100):
        content = ''
        for key, value in keyValueList:
            content += Log._getValueLine(key, value, indent)
            content += '\n'
        return content

    @staticmethod
    def _getFileAndLineInfo():
        _, modulepath, line, _, _, _ = inspect.stack()[2]
        content = '[' + os.path.basename(modulepath) + ':' + str(line) + ']: '
        return content

if __name__ == "__main__":
    ainst_logging.init('./aaaaaa', logging.DEBUG, logging.DEBUG)
    Log.cout(Log.INFO, 'hello')
    Log.coutValue(Log.INFO, 'hello', 'ainst', Log.USER_LOGGER)
    Log.coutLabel(Log.INFO, 'hello', Log.AINST_LOGGER)
