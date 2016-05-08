#! /usr/bin/python

from logger import Log
from aicf import AicfInfo

class AicfInfoWrapper:
    def removeConfigPrefix(self, aicfInfo):
        if not aicfInfo or len(aicfInfo.configs) == 0:
            return True

        configs = {}
        for destPath, configInfo in aicfInfo.configs.iteritems():
            if not destPath.startswith('/'):
                Log.cout(Log.ERROR, 'Aicf config has illegal prefix: %s' % destPath)
                return False
            destPath = destPath[len('/'):]
            if destPath == '':
                Log.cout(Log.ERROR, 'Aicf config has illegal prefix: %s' % destPath)
                return False
            if destPath.startswith('ainst/'):
                continue
            configInfo.destPath = destPath
            configs[destPath] = configInfo
        aicfInfo.configs = configs
        return True
