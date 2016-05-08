#! /usr/bin/python

import os
import file_util
from logger import Log
from package_util import PackageUtil
from ainst_root import AinstRoot, AinstRootReader
from root_executor import RootExecutor
from aicf import AicfConfigMode, AicfParser
from aicf_info_wrapper import AicfInfoWrapper
from setting_streamer import SettingStreamer

class RootActionExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryRun=False):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        self._pkg = pkg
        self._dryRun = dryRun
        self._ainstActivePkg = None
        self._ainstPkgDir = None

    def _getScriptContent(self, action):
        pkgDirName = PackageUtil.getPkgNameVersion(self._pkg)
        if not pkgDirName:
            Log.cout(Log.ERROR, 'Get pkg %s dir name failed' % self._pkg)
            return None

        self._ainstActivePkg = self._ainstRoot.getRootVarAinstDir('active') + self._pkg.name
        if not self._isActive(self._ainstActivePkg, pkgDirName):
            Log.cout(Log.ERROR, 'Package %s is not active' % self._pkg)
            return None

        self._ainstPkgDir = self._ainstRoot.getRootVarAinstDir('packages') + pkgDirName
        aicfFile = self._ainstPkgDir + '/ainst/' + self._pkg.name + '.aicf'
        if not file_util.isFile(aicfFile):
            return None

        aicfInfo = AicfParser().parse(aicfFile)
        if not aicfInfo or not AicfInfoWrapper().removeConfigPrefix(aicfInfo) \
                or not self._checkAicfInfo(aicfInfo):
            Log.cout(Log.ERROR, 'Aicf info of pkg %s is illegal' % self._pkg)
            return None

        if not aicfInfo.scripts.has_key(action):
            Log.cout(Log.ERROR, 'Pkg %s has no %s script' % (self._pkg, action))
            return None
        
        return aicfInfo.scripts[action]
        
    def _getSettings(self):
        settingsPath = self._ainstRoot.getRootVarAinstDir('settings') + self._pkg.name
        settings = SettingStreamer().parse(settingsPath)
        return settings

    def _doExecute(self, action):
        if not self._ainstRoot.checkRoot():
            Log.cout(Log.ERROR, 'Check ainst root failed')
            return False
        scriptContent = self._getScriptContent(action)
        if scriptContent is None:
            Log.cout(Log.ERROR, 'Get %s script of pkg %s failed' % (action, self._pkg))
            return False
        
        if self._dryRun:
            Log.coutValue(Log.INFO, '%s: ' % action, scriptContent)
            return True

        settings = self._getSettings()
        if settings is None:
            Log.cout(Log.ERROR, 'Parse settings of pkg %s  failed' % self._pkg)
            return False

        settingsEnv = self._generateSettingsEnv(settings)
        ainstDirPath = self._ainstPkgDir + '/ainst/'
        ainstPathEnv = {self._ainstDirKey : ainstDirPath}
        self._exportToEnv(ainstPathEnv)
        self._exportToEnv(settingsEnv)
        ret = self._processScript(scriptContent)
        self._removeFromEnv(settingsEnv)
        self._removeFromEnv(ainstPathEnv)

        return ret

    def undo(self):
        return True
        
class RootStartExecutor(RootActionExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryRun=False):
        RootActionExecutor.__init__(self, ainstRoot, ainstConf, pkg, dryRun)

    def execute(self):
        return self._doExecute('start')

class RootStopExecutor(RootActionExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryRun=False):
        RootActionExecutor.__init__(self, ainstRoot, ainstConf, pkg, dryRun)

    def execute(self):
        return self._doExecute('stop')

class RootRestartExecutor(RootActionExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryRun=False):
        RootActionExecutor.__init__(self, ainstRoot, ainstConf, pkg, dryRun)

    def execute(self):
        return self._doExecute('restart')

class RootReloadExecutor(RootActionExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryRun=False):
        RootActionExecutor.__init__(self, ainstRoot, ainstConf, pkg, dryRun)

    def execute(self):
        return self._doExecute('reload')
