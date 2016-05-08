#! /usr/bin/python

import os
import file_util
from logger import Log
from package_util import PackageUtil
from aicf import AicfParser
from config_generator import ConfigGenerator
from aicf_info_wrapper import AicfInfoWrapper
from setting_streamer import SettingStreamer
from root_set_base_executor import RootSetBaseExecutor

class RootUnsetExecutor(RootSetBaseExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, unsetKeySet, dryRun=False):
        RootSetBaseExecutor.__init__(self, ainstRoot, ainstConf)
        self._pkg = pkg
        self._unsetKeySet = unsetKeySet
        self._dryRun = dryRun
        self._bakSettings = None
        self._confBakDict = {}
        self._executed = False
        
    def execute(self):
        if self._dryRun:
            if self._unsetKeySet:
                Log.cout(Log.INFO, 'Unset pkg %s settings...' % self._pkg.name)
                for key in self._unsetKeySet:
                    Log.coutValue(Log.INFO, 'unset', key)
            return True
        if self._executed:
            return False
        self._executed = True

        if not self._ainstRoot.checkRoot():
            Log.cout(Log.ERROR, 'Check ainst root failed')
            return False

        pkgDirName = PackageUtil.getPkgNameVersion(self._pkg)
        if not pkgDirName:
            Log.cout(Log.ERROR, 'Get pkg %s dir name failed' % self._pkg)
            return False

        #get active dir and package dir
        ainstActivePkg = self._ainstRoot.getRootVarAinstDir('active') + self._pkg.name
        if not self._isActive(ainstActivePkg, pkgDirName):
            Log.cout(Log.ERROR, 'Package %s is not active' % self._pkg)
            return False
        ainstPkgDir = self._ainstRoot.getRootVarAinstDir('packages') + pkgDirName
        getRet, aicfInfo = self._getAicfInfo(ainstPkgDir, self._pkg)
        if not getRet:
            Log.cout(Log.ERROR, 'Get aicfInfo of %s failed' % self._pkg)
            return False            

        if aicfInfo is None:
            Log.cout(Log.INFO, 'No aicf, will not do effective action')
            return True

        #get settings from setting file
        settingPath = self._ainstRoot.getRootVarAinstDir('settings') + self._pkg.name
        srcSettings = SettingStreamer().parse(settingPath)
        if srcSettings is None:
            srcSettings = {}
        newSettings = self._unsetSettings(srcSettings, self._unsetKeySet)

        settingsEnv = self._generateSettingsEnv(newSettings)
        ainstDirPath = ainstPkgDir + '/ainst/'
        ainstPathEnv = {self._ainstDirKey : ainstDirPath}
        self._exportToEnv(ainstPathEnv)
        self._exportToEnv(settingsEnv)
        settingMap = {}
        settingMap.update(newSettings)
        settingMap[self._ainstRoot.getInstallRootEnvKey()] = self._ainstRoot.getRoot()
        settingMap.update(ainstPathEnv)
        ret = self._generateConfigToRoot(ainstPkgDir, aicfInfo,
                                         settingMap, self._confBakDict)
        self._removeFromEnv(settingsEnv)
        self._removeFromEnv(ainstPathEnv)

        if not ret:
            Log.cout(Log.ERROR, 'Generate config of %s to root failed' % self._pkg.name)
            self.undo()
            return False

        if not SettingStreamer().dump(newSettings, settingPath):
            Log.cout(Log.ERROR, 'Dump settings of %s failed' % self._pkg.name)
            self.undo()
            return False
        self._bakSettings = srcSettings
        return True

    def undo(self):
        if not self._executed:
            return False

        if self._bakSettings is not None:
            settingPath = self._ainstRoot.getRootVarAinstDir('settings') + self._pkg.name
            if not SettingStreamer().dump(self._bakSettings, settingPath):
                Log.cout(Log.ERROR, 'Rollback settings of pkg %s failed' % self._pkg.name)
                return False

        for src, dest in self._confBakDict.values():
            if not file_util.move(src, dest):
                return False
        
        self._confBakDict = {}
        self._bakSettings = None
        self._executed = False
        return True

    def _unsetSettings(self, srcSettings, unsetKeySet):
        result = {}
        result.update(srcSettings)
        for key in unsetKeySet:
            if result.has_key(key):
                del result[key]
        return result


if __name__ == '__main__':
    ainstRoot = AinstRoot('/home/larmmi.zhang/Install/')
    ainstRoot.init()
    settings = {'port':'9000', 'hash':'sha1', 'larmmi':'vivian'}
    executor = RootSetExecutor(ainstRoot, 'libredis', settings)
    executor.execute()
    executor.undo()
