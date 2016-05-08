#! /usr/bin/python

import os
from logger import Log
import file_util
import process
from bdb_wrapper import BdbWrapper

class RootExecutor:
    def __init__(self, ainstRoot, ainstConf):
        self._ainstRoot = ainstRoot
        self._ainstConf = ainstConf
        self._bakRpmPath = '/ainst/installed.rpm'
        self._ainstDirKey = 'AINST__AINSTDIR'

    def execute(self):
        return True

    def undo(self):
        return True

    def _processScript(self, content):
        if not content:
            return True
        Log.cout(Log.INFO, content)
        out, err, code = process.runRedirected(content)
        if out:
            Log.cout(Log.INFO, out)
        if err:
            Log.cout(Log.ERROR, err)
        return code == 0

    def _processScriptByName(self, scriptName):
        if not self._noExecute and self._aicfInfo and \
                self._aicfInfo.scripts.has_key(scriptName):
            scriptContent = self._aicfInfo.scripts[scriptName]
            self._exportToEnv(self._ainstPathEnv)
            ret = self._processScript(scriptContent)
            self._removeFromEnv(self._ainstPathEnv)
            if not ret:
                Log.cout(Log.ERROR, 'Process %s script failed' % scriptName)
                return False
        return True

    def _checkAicfInfo(self, aicfInfo):
        if not aicfInfo:
            return False

        for config in aicfInfo.configs.values():
            items = config.destPath.split('/')
            if len(items) < 2 or not self._ainstRoot.isInRootDir(items[0]):
                Log.cout(Log.ERROR, 'Invalid file path %s' % config.destPath)
                return False
        return True

    def _exportToEnv(self, envDict):
        if not envDict:
            return
        os.environ.update(envDict)

    def _removeFromEnv(self, envDict):
        if not envDict:
            return
        for key in envDict:
            if os.environ.has_key(key):
                del os.environ[key]

    def _generateSettingsEnv(self, settings):
        settingsEnv = {}
        if not settings:
            return settingsEnv
        for key, value in settings.iteritems():
            key = 'AINST__' + self._pkg.name + '__' + key
            settingsEnv[key] = value
        return settingsEnv

    def _getActiveRelativePath(self, pkgDirName):
        return '../packages/' + pkgDirName

    def _isActive(self, activePath, pkgDirName):
        relativePkgPath = self._getActiveRelativePath(pkgDirName)
        linkPath = file_util.readLink(activePath)
        if linkPath and linkPath == relativePkgPath:
            return True            
        return False

    def _getFilePkgDb(self):
        filePkgDbPath = self._ainstRoot.getFilePkgDbPath()
        return BdbWrapper(filePkgDbPath)

    def _getPkgFileDb(self):
        pkgFileDbPath = self._ainstRoot.getPkgFileDbPath()
        return BdbWrapper(pkgFileDbPath)

    def _getFileSpliter(self):
        return self._ainstRoot.getFileSpliter()

    def _returnAndCloseDb(self, ret, dbList):
        if not dbList:
            return ret
        for db in dbList:
            if db:
                db.close()
        return ret

class CompositeExecutor(RootExecutor):
    def __init__(self):
        self._executorList = []
        self._executedList = []

    def appendExecutor(self, executor):
        self._executorList.append(executor)

    def removeExecutor(self, removeExecutor):
        for executor in self._executorList:
            if executor == removeExecutor:
                self._executorList.remove(executor)

    def isExecuted(self):
        return len(self._executorList) == 0 and len(self._executedList) > 0

    def execute(self):
        success = True
        for executor in self._executorList:
            if not executor.execute():
                success = False
                break
            self._executedList.append(executor)
        tmpExecutorList = [x for x in self._executorList if x not in self._executedList]
        self._executorList = tmpExecutorList
        if not success:
            self.undo()
            return False
        return True
    
    def undo(self):
        for executedExecutor in self._executedList[::-1]:
            if not executedExecutor.undo():
                return False
            self._executorList.insert(0, executedExecutor)
        tmpExecutedList = [x for x in self._executedList if x not in self._executorList]
        self._executedList = tmpExecutedList
        return True


if __name__ == '__main__':
    installRoot = sys.argv[1]
    ainstRoot = AinstRoot(installRoot)
    ainstRoot.init()
    rpmPath = '/home/xiaoming.zhang/aicf/aggregator/build/release64/rpm_build/RPMS/x86_64/aggregator-3.9.1-rc_1.x86_64.rpm'
    from package_object import PackageObject
    class TestPkg(PackageObject):
        def __init__(self):
            PackageObject.__init__(self)
        def installed(self):
            return True    
        def active(self):
            return True
        def getLocation(self):
            return rpmPath
    package = TestPkg()
    package.name = 'aggregator'
    package.version = '3.9.1'
    package.release = 'rc_1'
    package.epoch = '0'
    package.arch = 'x86_64'

