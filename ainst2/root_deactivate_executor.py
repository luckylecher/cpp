#! /usr/bin/python

import os
import rpm
import rpmutils
import file_util
from logger import Log
from package_util import PackageUtil
from rpm_file_wrapper import RpmFileWrapper
from aicf import AicfParser
from setting_streamer import SettingStreamer
from aicf_info_wrapper import AicfInfoWrapper
from root_executor import RootExecutor

class RootDeactivateExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf, 
                 pkg, noStop=False, noExecute=False,
                 settings={}, dryrun=False):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        self._pkg = pkg
        self._noStop = noStop
        self._noExecute = noExecute
        self._dryrun = dryrun
        self._cliSettings = settings
        self._init()

    def _init(self):
        self._executed = False
        self._ainstActivePkg = None
        self._ainstPkgDir = None
        self._aicfInfo = None
        self._ainstPathEnv = {}
        self._settingsEnv = {}
        self._lastActivePkg = None
        self._modifyDb = False
        self._crontabSrcDest = None
        self._pkgFiles = None
        self._fileList = None
        self._unlinkList = []
        self._rmdirList = []
        self._confDict = {}
        self._success = False

    def execute(self):
        Log.cout(Log.INFO, 'Deactivate pkg %s ...' % self._pkg)
        if self._dryrun:
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

        self._ainstActivePkg = self._ainstRoot.getRootVarAinstDir('active') + self._pkg.name
        self._ainstPkgDir = self._ainstRoot.getRootVarAinstDir('packages') + pkgDirName
        if not self._isActive(self._ainstActivePkg, pkgDirName):
            Log.cout(Log.INFO, 'Package %s is always deactive' % self._pkg)
            return True

        ainstDirPath = self._ainstPkgDir + '/ainst/'
        self._ainstPathEnv = {self._ainstDirKey : ainstDirPath}
        aicfFile = ainstDirPath + self._pkg.name + '.aicf'
        if file_util.isFile(aicfFile):
            self._aicfInfo = AicfParser().parse(aicfFile)
            if not self._aicfInfo or not AicfInfoWrapper().removeConfigPrefix(self._aicfInfo) \
                    or not self._checkAicfInfo(self._aicfInfo):
                Log.cout(Log.ERROR, 'Aicf info of pkg %s is illegal' % self._pkg)
                return False

        #calc settings
        settingPath = self._ainstRoot.getRootVarAinstDir('settings') + self._pkg.name
        settings = SettingStreamer().parse(settingPath)
        if settings is None:
            Log.cout(Log.ERROR, 'Parse settings of pkg %s  failed' % self._pkg)
            return False
        useSettings = self._mergeSettings(settings, self._cliSettings)
        self._settingsEnv = self._generateSettingsEnv(useSettings)

        self._processStopScript()
        if not self._processScriptByName('pre-deactivate'):
            self.undo()
            return False

        #get rpm file infos
        bakRpmFile = self._ainstPkgDir + self._ainstRoot.getBackRpmPath()
        rpmFileInfoList = RpmFileWrapper().convert(bakRpmFile)
        if rpmFileInfoList is None:
            Log.cout(Log.ERROR, 'Get rpm file info failed: %s', bakRpmFile)
            self.undo()
            return False

        ret, self._lastActivePkg = self._unSymlinkFromActive(self._ainstActivePkg)
        if not ret:
            Log.cout(Log.ERROR, 'UnsymLink pkg %s dir from active failed' % self._pkg)
            self.undo()
            return False

        if not self._unlinkPkgFromRoot(rpmFileInfoList, self._unlinkList,
                                       self._rmdirList, self._confDict):
            Log.cout(Log.ERROR, 'Unink pkg %s dir from root failed' % self._pkg)
            self.undo()
            return False

        if not self._removeCrontabFile():
            Log.cout(Log.ERROR, 'Remove crontab file of pkg %s failed' % self._pkg)
            self.undo()
            return False            

        self._modifyDb = self._removeFileFromDb()
        if not self._modifyDb:
            Log.cout(Log.ERROR, 'Modify db failed')
            self.undo()
            return False

        if not self._processScriptByName('post-deactivate'):
            self.undo()
            return False

        self._success = True
        Log.cout(Log.DEBUG, 'Deactivate pkg %s success' % self._pkg)
        return True

    def undo(self):
        if self._dryrun:
            return True
        if not self._executed:
            return False
        Log.cout(Log.INFO, 'Undo deactivate pkg %s ...' % self._pkg)

        if self._success:
            if not self._noExecute and not self._processScriptByName('pre-activate'):
                return False

        # roll back unlink from root
        for dest in self._rmdirList:
            if not file_util.makeDir(dest):
                return False
        for src, dest in self._unlinkList:
            if not file_util.link(src, dest):
                return False
        for src, dest in self._confDict.values():
            if not file_util.move(src, dest):
                return False

        if self._modifyDb and not self._addFileToDb():
                return False

        if self._crontabSrcDest:
            cronFilePath, tmpPath = self._crontabSrcDest
            if not file_util.move(tmpPath, cronFilePath):
                return False
        
        # roll back unlink from active
        if self._lastActivePkg:
            if not file_util.symLink(self._lastActivePkg, self._ainstActivePkg):
                return False

        if self._success:
            if not self._noExecute and not self._processScriptByName('post-activate'):
                return False

        # roll back stop
        if not self._noExecute and not self._noStop and self._aicfInfo and\
                self._aicfInfo.autoStart and self._aicfInfo.scripts.has_key('start'):
            scriptContent = self._aicfInfo.scripts['start']
            if scriptContent:
                self._exportToEnv(self._ainstPathEnv)
                self._exportToEnv(self._settingsEnv)
                self._processScript(scriptContent)
                self._removeFromEnv(self._settingsEnv)
                self._removeFromEnv(self._ainstPathEnv)

        self._init()
        return True

    def _mergeSettings(self, settings, cliSettings):
        if not cliSettings:
            return settings
        result = {}
        result.update(settings)
        result.update(cliSettings)
        for key, value in result.items():
            if value == '':
                del result[key]
        return result

    def _removeDir(self, dirName, rmdirList, recursive=True):
        if not dirName or not dirName.startswith(self._ainstRoot.getRoot()):
            Log.cout(Log.ERROR, 'Remove invalid path %s' % dirName)
            return False
        if dirName[-1] != '/':
            dirName += '/'
        if self._ainstRoot.isAinstDir(dirName):
            Log.cout(Log.DEBUG, 'Ainst root path %s need not remove' % dirName)
            return True
        subDirs = file_util.listDir(dirName)
        if subDirs is not None and len(subDirs) == 0:
            if not file_util.remove(dirName):
                Log.cout(Log.ERROR, 'Remove dir %s failed' % dirName)
                return False
            rmdirList.append(dirName)
            if recursive:
                dirPath = os.path.dirname(dirName[:-1])
                return self._removeDir(dirPath, rmdirList, recursive)
        return True

    def _unlinkPkgFromRoot(self, rpmFileInfoList, unlinkList, rmdirList, confDict):
        if self._aicfInfo:
            for path in self._aicfInfo.configs.keys():
                destConfigPath = self._ainstRoot.getRoot() + '/' + path
                if file_util.isFile(destConfigPath):
                    tmpDirName = self._ainstRoot.getRootVarAinstDir('tmp')
                    tmpPath = tmpDirName + '/' + os.path.basename(destConfigPath) + '.tmp'
                    if not file_util.move(destConfigPath, tmpPath):
                        return False
                    confDict[path] = (tmpPath, destConfigPath)
                    dirName = os.path.dirname(destConfigPath) + '/'
                    if not self._removeDir(dirName, rmdirList):
                        return False
        for rpmFileInfo in rpmFileInfoList:
            srcPath = self._ainstPkgDir + '/' + rpmFileInfo.relativePath
            destPath = self._ainstRoot.getRoot() + '/' + rpmFileInfo.relativePath
            if rpmFileInfo.isDir:
                if not self._removeDir(destPath, rmdirList, False):
                    return False
            elif not rpmFileInfo.isConfigFile():
                if not file_util.remove(destPath):
                    return False
                unlinkList.append((srcPath, destPath))
                if not self._removeDir(os.path.dirname(destPath) + '/', rmdirList):
                    return False
            else:
                if confDict.has_key(rpmFileInfo.relativePath):
                    continue
                if file_util.isFile(destPath):
                    dirName = self._ainstRoot.getRootVarAinstDir('tmp')
                    tmpPath = dirName + os.path.basename(destPath) + '.tmp'
                    if not file_util.move(destPath, tmpPath):
                        return False
                    confDict[rpmFileInfo.relativePath] = (tmpPath, destPath)
                    if not self._removeDir(os.path.dirname(destPath) + '/', rmdirList):
                        return False
        return True

    def _unSymlinkFromActive(self, ainstActivePkg):
        if file_util.isLink(ainstActivePkg):
            lastActivePkg = file_util.readLink(ainstActivePkg)
        if not file_util.remove(ainstActivePkg):
            return False, None
        return True, lastActivePkg

    def _removeFileFromDb(self):
        filePkgDb = self._getFilePkgDb()
        pkgFileDb = self._getPkgFileDb()
        if not filePkgDb.open() or not pkgFileDb.open():
            return self._returnAndCloseDb(False, [filePkgDb, pkgFileDb])

        ret, self._pkgFiles = pkgFileDb.removeAndReturnOldValue(self._pkg.name)
        if self._pkgFiles:
            self._fileList = self._pkgFiles.split(self._getFileSpliter())
            for fileName in self._fileList:
                filePkgDb.remove(fileName)
        return self._returnAndCloseDb(True, [filePkgDb, pkgFileDb])

    def _addFileToDb(self):
        filePkgDb = self._getFilePkgDb()
        pkgFileDb = self._getPkgFileDb()
        if not filePkgDb.open() or not pkgFileDb.open():
            return self._returnAndCloseDb(False, [filePkgDb, pkgFileDb])

        if self._fileList:
            for fileName in self._fileList:
                filePkgDb.set(fileName, self._pkg.name)
        pkgFileDb.set(self._pkg.name, self._pkgFiles)
        return self._returnAndCloseDb(True, [filePkgDb, pkgFileDb])

    def _processStopScript(self):
        if not self._noExecute and not self._noStop and self._aicfInfo and\
                self._aicfInfo.autoStart and self._aicfInfo.scripts.has_key('stop'):
            scriptContent = self._aicfInfo.scripts['stop']
            if scriptContent:
                self._exportToEnv(self._ainstPathEnv)
                self._exportToEnv(self._settingsEnv)
                self._processScript(scriptContent)
                self._removeFromEnv(self._settingsEnv)
                self._removeFromEnv(self._ainstPathEnv)

    def _removeCrontabFile(self):
        cronFilePath = self._ainstRoot.getRootVarDir('cron') + self._pkg.name
        if file_util.exists(cronFilePath):
            tmpDirName = self._ainstRoot.getRootVarAinstDir('tmp')
            tmpPath = tmpDirName + '/' + self._pkg.name + '.crontab.tmp'
            if not file_util.move(cronFilePath, tmpPath):
                return False
            self._crontabSrcDest = (cronFilePath, tmpPath)
        return True
