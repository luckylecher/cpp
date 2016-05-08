#! /usr/bin/python

import os
import file_util
from logger import Log
from aicf import AicfParser
from config_generator import ConfigGenerator
from aicf_info_wrapper import AicfInfoWrapper
from root_executor import RootExecutor

class RootSetBaseExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        
    def _getAicfInfo(self, ainstPkgDir, pkg):
        aicfFile = ainstPkgDir + '/ainst/' + pkg.name + '.aicf'
        if file_util.isFile(aicfFile):
            aicfInfo = AicfParser().parse(aicfFile)
            if not aicfInfo or not AicfInfoWrapper().removeConfigPrefix(aicfInfo) \
                    or not self._checkAicfInfo(aicfInfo):
                Log.cout(Log.ERROR, 'Aicf info of pkg %s is illegal' % pkg.name)
                return False, None
            return True, aicfInfo
        return True, None

    def _generateConfigToRoot(self, ainstPkgDir, aicfInfo, settingMap, confDict):
        if aicfInfo:
            for path, configInfo in aicfInfo.configs.iteritems():
                srcConfigPath = ainstPkgDir + '/' + path
                destConfigPath = self._ainstRoot.getRoot() + '/' + path
                if not file_util.isFile(srcConfigPath):
                    Log.cout(Log.ERROR, 'Config file %s is not exists' % srcConfigPath)
                    return False
                if not file_util.exists(destConfigPath):
                    Log.cout(Log.ERROR, 'Dest config file %s is not exists' % destConfigPath)
                    return False
                tmpDirName = self._ainstRoot.getRootVarAinstDir('tmp')
                tmpPath = tmpDirName + '/' + os.path.basename(destConfigPath) + '.tmp.set'
                if not file_util.move(destConfigPath, tmpPath):
                    Log.cout(Log.ERROR, 'Backup config file %s failed' % destConfigPath)
                    return False
                confDict[path] = (tmpPath, destConfigPath)
                configGenerator = ConfigGenerator()
                if not configGenerator.generateConfig(srcConfigPath, 
                                                      destConfigPath, 
                                                      configInfo.mode, 
                                                      configInfo.noReplace,
                                                      settingMap):
                    Log.cout(Log.ERROR, 'Generate Config file %s failed' % path)
                    return False
        else:
            Log.cout(Log.DEBUG, 'No aicf file, so no config will be changed')
        return True

