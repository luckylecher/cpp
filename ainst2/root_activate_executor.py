#! /usr/bin/python

import re
import os
import rpmutils
import file_util
from logger import Log
from package_util import PackageUtil
from rpm_file_wrapper import RpmFileWrapper
from aicf import AicfParser
from config_generator import ConfigGenerator
from aicf_info_wrapper import AicfInfoWrapper
from setting_streamer import SettingStreamer
from root_executor import RootExecutor

class RootActivateExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, noStart=False, 
                 noExecute=False, settings={}, dryrun=False, unsetKey=set()):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        self._pkg = pkg
        self._noStart = noStart
        self._noExecute = noExecute
        self._dryrun = dryrun
        self._cliSettings = settings
        self._unsetKeySet = unsetKey
        self._init()

    def _init(self):
        self._executed = False
        self._ainstActivePkg = None
        self._ainstPkgDir = None
        self._aicfInfo = None
        self._backSettings = None
        self._modifyDb = False
        self._generatedCrontab = False
        self._ainstPathEnv = {}
        self._settingsEnv = {}
        self._linkList = []
        self._mkdirList = []
        self._confSet = set()
        self._linkToActive = False
        self._lastActivePkg = None
        self._success = False

    def execute(self):
        Log.cout(Log.INFO, 'Activate pkg %s ...' % self._pkg)
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

        #get active dir and package dir
        self._ainstActivePkg = self._ainstRoot.getRootVarAinstDir('active') + self._pkg.name
        if self._isActive(self._ainstActivePkg, pkgDirName):
            Log.cout(Log.INFO, 'Package %s is always active' % self._pkg)
            return True            
        self._ainstPkgDir = self._ainstRoot.getRootVarAinstDir('packages') + pkgDirName
        if not file_util.isDir(self._ainstPkgDir):
            Log.cout(Log.ERROR, 'Package %s is not installed' % self._pkg)
            return False

        #get aicf info
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
        backSettings = SettingStreamer().parse(settingPath)
        if backSettings is None:
            Log.cout(Log.ERROR, 'Parse settings of pkg %s  failed' % self._pkg)
            return False
        useSettings = {}
        useSettings.update(backSettings)
        self._mergeSettings(useSettings, self._aicfInfo, self._cliSettings,
                            self._unsetKeySet)

        self._settingsEnv = self._generateSettingsEnv(useSettings)

        #get rpm file infos
        bakRpmFile = self._ainstPkgDir + self._ainstRoot.getBackRpmPath()
        rpmFileInfoList = RpmFileWrapper().convert(bakRpmFile)
        if rpmFileInfoList is None:
            Log.cout(Log.ERROR, 'Get rpm file info failed: %s', bakRpmFile)
            return False

        if not self._processScriptByName('pre-activate'):
            return False

        #link common files and makedir if needed
        if not self._linkPkgToRoot(rpmFileInfoList, self._linkList, self._mkdirList):
            Log.cout(Log.ERROR, 'Link pkg %s dir to root failed' % self._pkg)
            self.undo()
            return False

        #generate a new config file and copy to root dir
        self._exportToEnv(self._ainstPathEnv)
        self._exportToEnv(self._settingsEnv)
        settingMap = {}
        settingMap.update(useSettings)
        settingMap[self._ainstRoot.getInstallRootEnvKey()] = self._ainstRoot.getRoot()
        settingMap.update(self._ainstPathEnv)
        ret = self._generateConfigToRoot(rpmFileInfoList, self._aicfInfo, 
                                         settingMap, self._confSet)
        self._removeFromEnv(self._settingsEnv)
        self._removeFromEnv(self._ainstPathEnv)
        if not ret:
            Log.cout(Log.ERROR, 'Generate config of pkg %s failed' % self._pkg)
            self.undo()
            return False

        #seralize to setting files
        if len(useSettings) > 0:
            if not SettingStreamer().dump(useSettings, settingPath):
                Log.cout(Log.ERROR, 'Save settings of pkg %s failed' % self._pkg)
                self.undo()
                return False
            self._backSettings = backSettings

        self._modifyDb = self._addFileToDb()
        if not self._modifyDb:
            Log.cout(Log.ERROR, 'Modify db failed')
            self.undo()
            return False

        if not self._generateCrontabFile():
            Log.cout(Log.ERROR, 'Generate crontab failed')
            self.undo()
            return False

        #do symbol link from package dir to active dir
        relativePkgPath = self._getActiveRelativePath(pkgDirName)
        self._linkToActive, self._lastActivePkg = self._symLinkToActive(relativePkgPath,
                                                                        self._ainstActivePkg)
        if not self._linkToActive:
            Log.cout(Log.ERROR, 'SymLink pkg %s dir to active failed' % self._pkg)
            self.undo()
            return False

        if not self._processScriptByName('post-activate'):
            self.undo()
            return False
        self._processStartScript(useSettings)

        self._success = True
        Log.cout(Log.DEBUG, 'Activate pkg %s success' % self._pkg)
        return True

    def undo(self):
        if self._dryrun:
            return True
        if not self._executed:
            return False
        Log.cout(Log.INFO, 'Undo activate pkg %s ...' % self._pkg)
        if self._success:
            if not self._noExecute and not self._noStart and self._aicfInfo and\
                    self._aicfInfo.autoStart and self._aicfInfo.scripts.has_key('stop'):
                scriptContent = self._aicfInfo.scripts['stop']
                if scriptContent:
                    self._exportToEnv(self._ainstPathEnv)
                    self._exportToEnv(self._settingsEnv)
                    self._processScript(scriptContent)
                    self._removeFromEnv(self._settingsEnv)
                    self._removeFromEnv(self._ainstPathEnv)

            if not self._noExecute and not self._processScriptByName('pre-deactivate'):
                return False

        # roll back symlink to active
        if self._linkToActive:
            if not file_util.remove(self._ainstActivePkg):
                return False
        if self._lastActivePkg:
            if not file_util.link(self._lastActivePkg, self._ainstActivePkg):
                return False

        if self._generatedCrontab:
            crontabFile = self._ainstRoot.getRootVarDir('cron') + self._pkg.name
            if not file_util.remove(crontabFile):
                return False

        if self._modifyDb:
            if not self._removeFileFromDb():
                return False

        if self._backSettings is not None:
            settingPath = self._ainstRoot.getRootVarAinstDir('settings') + self._pkg.name
            if not SettingStreamer().dump(self._backSettings, settingPath):
                Log.cout(Log.ERROR, 'Save settings of pkg %s failed' % self._pkg)
                return False

        #roll back config file
        for path in self._confSet:
            if not file_util.remove(self._ainstRoot.getRoot() + '/' + path):
                return False

        # roll back link to root
        for dest in self._linkList[::-1]:
            destPath = self._ainstRoot.getRoot() + '/' + dest
            if not file_util.remove(destPath):
                return False
        for destDir in self._mkdirList[::-1]:
            if not file_util.remove(destDir):
                return False
            
        if self._success:
            if not self._noExecute and not self._processScriptByName('post-deactivate'):
                return False

        self._init()
        return True

    def _mergeSettings(self, srcSettings, aicfInfo, addSettings, unsetKey):
        aicfSettings = {}
        aicfUnSettings = {}
        if aicfInfo:
            aicfSettings = aicfInfo.settings
            aicfUnSettings = aicfInfo.unSettings
        if addSettings is None:
            addSettings = {}
        if unsetKey is None:
            unsetKey = set()

        for key, value in aicfSettings.iteritems():
            if key in aicfUnSettings:
                aicfUnSettings.remove(key)
                continue
            if not srcSettings.has_key(key):
                srcSettings[key] = value

        for key in aicfUnSettings:
            if srcSettings.has_key(key):
                del srcSettings[key]

        srcSettings.update(addSettings)
        for key in unsetKey:
            if srcSettings.has_key(key) and not addSettings.has_key(key):
                del srcSettings[key]
        return True

    def _symLinkToActive(self, relativePkgPath, ainstActivePkg):
        lastActivePkg = file_util.readLink(ainstActivePkg)
        if not file_util.remove(ainstActivePkg):
            return False, None
        if not file_util.symLink(relativePkgPath, ainstActivePkg):
            return False, lastActivePkg
        return True, lastActivePkg

    def _linkPkgToRoot(self, rpmFileInfoList, linkList, mkdirList):
        for rpmFileInfo in rpmFileInfoList:
            items = rpmFileInfo.relativePath.split('/')
            if len(items) < 2:
                Log.cout(Log.ERROR, 'Invalid file path %s' % rpmFileInfo.relativePath)
                return False                

            # disable dir check
            # if items[0] != 'ainst' and not self._ainstRoot.isInRootDir(items[0]):
            #     Log.cout(Log.ERROR, 'Invalid file path %s' % rpmFileInfo.relativePath)
            #     return False

            if rpmFileInfo.isDir:
                dirPath = self._ainstRoot.getRoot() + '/' + rpmFileInfo.relativePath
                ret, dirList = file_util.makeDir2(dirPath)
                if not ret:
                    Log.cout(Log.ERROR, 'Makedir %s failed' % dirName)
                    return False
                mkdirList.extend(dirList)
            else:
                srcPath = self._ainstPkgDir + '/' + rpmFileInfo.relativePath
                destPath = self._ainstRoot.getRoot() + '/' + rpmFileInfo.relativePath
                if not file_util.isLink(srcPath) and not file_util.exists(srcPath):
                    Log.cout(Log.ERROR, 'Activate failed: not exists file %s' % srcPath)
                    return False
                if file_util.exists(destPath):
                    if self._isActiveFile(rpmFileInfo.relativePath) or\
                            not file_util.remove(destPath):
                        Log.cout(Log.ERROR, 'File conflict %s, ignore and continue.' % destPath)
                        continue
                dirPath = os.path.dirname(destPath)
                ret, dirList = file_util.makeDir2(dirPath)
                if not ret:
                    Log.cout(Log.ERROR, 'Makedir %s failed' % dirName)
                    return False
                mkdirList.extend(dirList)
                if not rpmFileInfo.isConfigFile():
                    if not file_util.link(srcPath, destPath):
                        return False
                    linkList.append(rpmFileInfo.relativePath)
        return True

    def _generateConfigToRoot(self, rpmFileInfoList, aicfInfo, settingMap, confSet):
        configGenerator = ConfigGenerator()
        if aicfInfo:
            for path, configInfo in aicfInfo.configs.iteritems():
                srcConfigPath = self._ainstPkgDir + '/' + path
                destConfigPath = self._ainstRoot.getRoot() + '/' + path
                if not file_util.isFile(srcConfigPath):
                    Log.cout(Log.ERROR, 'Config file %s is not exists in pkg' % srcConfigPath)
                    return False
                if not file_util.remove(destConfigPath):
                    Log.cout(Log.ERROR, 'Remove path %s failed in pkg' % destConfigPath)
                    return False
                if not configGenerator.generateConfig(srcConfigPath, 
                                                      destConfigPath, 
                                                      configInfo.mode, 
                                                      configInfo.noReplace,
                                                      settingMap):
                    Log.cout(Log.ERROR, 'Generate Config file %s failed' % path)
                    return False
                confSet.add(path)

        for rpmFileInfo in rpmFileInfoList:
            if rpmFileInfo.isConfigFile():
                path = rpmFileInfo.relativePath
                if path in confSet:
                    continue
                srcConfigPath = self._ainstPkgDir + '/' + path
                destConfigPath = self._ainstRoot.getRoot() + '/' + path
                if not file_util.isFile(srcConfigPath):
                    Log.cout(Log.ERROR, 'Config file %s is not exists in pkg' % srcConfigPath)
                    return False
                if not configGenerator.generateConfig(srcConfigPath, destConfigPath):
                    Log.cout(Log.ERROR, 'Generate Config file %s failed' % path)
                    return False
                confSet.add(path)

        return True

    def _addFileToDb(self):
        filePkgDb = self._getFilePkgDb()
        pkgFileDb = self._getPkgFileDb()
        if not filePkgDb.open() or not pkgFileDb.open():
            return self._returnAndCloseDb(False, [filePkgDb, pkgFileDb])

        files = pkgFileDb.get(self._pkg.name)
        if files:
            fileList = files.split(self._getFileSpliter())
            for fileName in fileList:
                filePkgDb.remove(fileName)

        self._addFiles = self._confSet.union(set(self._linkList))
        for fileName in self._addFiles:
            filePkgDb.set(fileName, self._pkg.name)

        pkgFileDb.set(self._pkg.name, self._getFileSpliter().join(self._addFiles))
        return self._returnAndCloseDb(True, [filePkgDb, pkgFileDb])

    def _removeFileFromDb(self):
        filePkgDb = self._getFilePkgDb()
        pkgFileDb = self._getPkgFileDb()
        if not filePkgDb.open() or not pkgFileDb.open():
            return self._returnAndCloseDb(False, [filePkgDb, pkgFileDb])

        pkgFileDb.remove(self._pkg.name)
        for fileName in self._addFiles:
            filePkgDb.remove(fileName)
        return self._returnAndCloseDb(True, [filePkgDb, pkgFileDb])

    def _isActiveFile(self, fileName):
        filePkgDb = self._getFilePkgDb()
        if not filePkgDb.open():
            return False
        pkgName = filePkgDb.get(fileName)
        if pkgName is None:
            return self._returnAndCloseDb(False, [filePkgDb])
        self._ainstActivePkg = self._ainstRoot.getRootVarAinstDir('active') + pkgName
        linkPath = file_util.readLink(self._ainstActivePkg)
        if linkPath and linkPath.startswith('../packages/'):
            return self._returnAndCloseDb(True, [filePkgDb])
        return self._returnAndCloseDb(False, [filePkgDb])

    def _processStartScript(self, useSettings):
        if not self._noExecute and not self._noStart and self._aicfInfo and \
                self._aicfInfo.scripts.has_key('start') and self._aicfInfo.autoStart:
            scriptContent = self._aicfInfo.scripts['start']
            self._exportToEnv(self._ainstPathEnv)
            self._exportToEnv(self._settingsEnv)
            self._processScript(scriptContent)
            self._removeFromEnv(self._settingsEnv)
            self._removeFromEnv(self._ainstPathEnv)

    def _generateCrontabFile(self):
        if not self._aicfInfo or not self._aicfInfo.crontabs:
            return True

        content = ''
        content += self._ainstRoot.getInstallRootEnvKey() + \
            '=' + self._ainstRoot.getRoot() + '\n'
        ainstPath = self._ainstPkgDir + '/ainst/'
        content += self._ainstDirKey + '=' + ainstPath + '\n'
        for crontab in self._aicfInfo.crontabs:
            content += crontab + '\n'

        crontabFile = self._ainstRoot.getRootVarDir('cron') + self._pkg.name
        if not file_util.remove(crontabFile) or\
                not file_util.writeToFile(crontabFile, content):
            Log.cout(Log.ERROR, 'Generate crontab file %s failed' % crontabFile)
            return False
        self._generatedCrontab = True
        return True

