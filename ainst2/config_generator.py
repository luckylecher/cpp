#! /usr/bin/python

import re
import os
import file_util
import process
from logger import Log
from aicf import AicfConfigMode

class ConfigGenerator:
    def generateConfig(self, srcPath, destPath, mode=AicfConfigMode.NONE_MODE, 
                       noReplace=False, settings=None):
        if mode == AicfConfigMode.NONE_MODE:
            return self._generateConfigByCopy(srcPath, destPath)
        elif mode == AicfConfigMode.EXPAND_MODE:
            return self._generateConfigByExpand(srcPath, destPath, 
                                                noReplace, settings)
        elif mode == AicfConfigMode.TEMPLATE_MODE:
            return self._generateConfigByTemplate(srcPath, destPath, 
                                                  noReplace, settings)
        else:
            Log.cout(Log.ERROR, 'Invalid aicf config mode')
            return False

    def _generateConfigByCopy(self, srcPath, destPath):
        if not file_util.copyFile(srcPath, destPath):
            Log.cout(Log.ERROR, 'Generat config file %s failed' % destPath)
            return False
        return True

    def _generateConfigByExpand(self, srcPath, destPath, noReplace, settings):
        content = file_util.readFromFile(srcPath)
        if content is None:
            Log.cout(Log.ERROR, 'Read config file %s failed' % srcPath)
            return False
        replacer = KeyValueReplacer(settings)
        content = replacer.replace(content)
        return file_util.writeToFile(destPath, content)
    
    def _generateConfigByTemplate(self, srcPath, destPath, noReplace, settings):
        out, err, code = process.runRedirected(srcPath)
        if code != 0:
            Log.cout(Log.ERROR, 'Generat template config file %s failed: %s' % (destPath, err))
            return False
        if not file_util.writeToFile(destPath, out):
            Log.cout(Log.ERROR, 'Write config file to %s failed' % destPath)
            return False
        return True

class KeyValueReplacer:
    def __init__(self, keyValues):
        self._keyValues = keyValues

    def replace(self, content):
        keyPattern = ''
        for key in self._keyValues.keys():
            if keyPattern:
                keyPattern += '|'
            keyPattern += '\$\(' + re.escape(key) + '\)'
        return re.sub(keyPattern, self._replaceFunc, content)

    def _replaceFunc(self, matchObj):
        key = matchObj.group(0)
        return self._keyValues[key[2:-1]]
