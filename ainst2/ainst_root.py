#! /usr/bin/python

import re
import os
import time
import common
import rpmutils
import file_util
from bdb_wrapper import BdbWrapper
from root_state import RootState, RootStateStreamer
from setting_streamer import SettingStreamer

class AinstRoot:
    def __init__(self, root):
        self._root = root
        self._rootDir = ['bin', 'bin64', 'conf', 'doc', 'etc', 'include',
                         'include64', 'info', 'lib', 'lib64', 'libdata',
                         'libexec', 'libexec64', 'logs', 'man', 'sbin',
                         'sbin64', 'share', 'src', 'tmp', 'var', 'usr']
        self._rootVarDir = ['cron', 'run', 'ainst']
        self._rootVarAinstDir = ['active', 'config', 'log', 'save',
                                 'settings', 'packages', 'tmp', '.db']
        self._rootDirs = {}
        self._rootVarDirs = {}
        self._rootVarAinstDirs = {}
        self._filePkgDbName = 'file_pkg'
        self._pkgFileDbName = 'pkg_file'
        self._fileSpliter = ''
        self._installRootEnvKey = 'AINST__INSTALLROOT'
        self._backRpmPath = '/ainst/installed.rpm'
        self._ainstRootMarkFile = '.ainstroot'
        self._inited = False
        self._clearTmp = False
        self._initRootDirs()

    def isValidAinstRoot(self):
        return file_util.isFile(self._root + '/' + self._ainstRootMarkFile)

    def isAvailableAinstRoot(self):
        if not file_util.isDir(self._root):
            return True
        subDirs = file_util.listDir(self._root)
        if subDirs is not None and len(subDirs) == 0:
            return True
        return self.isValidAinstRoot()

    def init(self):
        if self._inited:
            return True, None

        if not self._root:
            return False, None

        markFilePath = self._root + '/' + self._ainstRootMarkFile
        initTrace = []
        if not file_util.isDir(self._root):
            if not file_util.makeDir(self._root):
                self.clearInit(initTrace)
                return False, None
            initTrace.append(self._root)
            if not file_util.writeToFile(markFilePath, ''):
                self.clearInit(initTrace)
                return False, None
            initTrace.append(markFilePath)
        else:
            if not file_util.isFile(markFilePath):
                subDirs = file_util.listDir(self._root)
                if subDirs and len(subDirs) > 0:
                    self.clearInit(initTrace)
                    return False, None
                if not file_util.writeToFile(markFilePath, ''):
                    self.clearInit(initTrace)
                    return False, None
                initTrace.append(markFilePath)

        if not self._initRoot(initTrace):
            return False, None
        os.environ[self._installRootEnvKey] = self._root
        self._inited = True
        return True, initTrace

    def _initRoot(self, initTrace):
        for name in self._rootDirs:
            if file_util.isDir(self._rootDirs[name]):
                continue
            if not file_util.makeDir(self._rootDirs[name]):
                self.clearInit(initTrace)
                return False
            initTrace.append(self._rootDirs[name])

        for name in self._rootVarDirs:
            if file_util.isDir(self._rootVarDirs[name]):
                continue
            if not file_util.makeDir(self._rootVarDirs[name]):
                self.clearInit(initTrace)
                return False
            initTrace.append(self._rootVarDirs[name])

        for name in self._rootVarAinstDirs:
            if file_util.isDir(self._rootVarAinstDirs[name]):
                continue
            if not file_util.makeDir(self._rootVarAinstDirs[name]):
                self.clearInit(initTrace)
                return False
            initTrace.append(self._rootVarAinstDirs[name])

        initRootState = self._rootVarAinstDirs['save'] + 'root-state-0'
        if not file_util.exists(initRootState):
            state = RootState(time.time(), '', self._root,
                              common.AINST_VERSION, [], {})
            content = RootStateStreamer().toString(state)
            if not content or not file_util.writeToFile(initRootState, content):
                self.clearInit(initTrace)
                return False
            initTrace.append(initRootState)

        if not self._clearTmp:
            if not file_util.remove(self._rootVarAinstDirs['tmp']) or\
                    not file_util.makeDir(self._rootVarAinstDirs['tmp']):
                self.clearInit(initTrace)
                return False
            self._clearTmp = True
        return True

    def clearInit(self, initTrace):
        for path in initTrace[::-1]:
            file_util.remove(path)
        self._inited = False

    def checkRoot(self):
        if not self._root:
            return False
        if not file_util.isFile(self._root + '/' + self._ainstRootMarkFile):
            return False
        for name in self._rootDirs:
            if not file_util.isDir(self._rootDirs[name]):
                return False

        for name in self._rootVarDirs:
            if not file_util.isDir(self._rootVarDirs[name]):
                return False

        for name in self._rootVarAinstDirs:
            if not file_util.isDir(self._rootVarAinstDirs[name]):
                return False

        initRootState = self._rootVarAinstDirs['save'] + 'root-state-0'
        if not file_util.exists(initRootState):
            return False
        os.environ[self._installRootEnvKey] = self._root
        return True

    def getBackRpmPath(self):
        return self._backRpmPath

    def getInstallRootEnvKey(self):
        return self._installRootEnvKey

    def getFilePkgDbPath(self):
        return self._rootVarAinstDirs['.db'] + self._filePkgDbName

    def getPkgFileDbPath(self):
        return self._rootVarAinstDirs['.db'] + self._pkgFileDbName
    
    def getFileSpliter(self):
        return self._fileSpliter

    def getRoot(self):
        return self._root

    def getRootDir(self, subDir):
        if self._rootDirs.has_key(subDir):
            return self._rootDirs[subDir]
        return None

    def getRootVarDir(self, subDir):
        if self._rootVarDirs.has_key(subDir):
            return self._rootVarDirs[subDir]
        return None

    def getRootVarAinstDir(self, subDir):
        if self._rootVarAinstDirs.has_key(subDir):
            return self._rootVarAinstDirs[subDir]
        return None

    def getRootDirs(self):
        return self._rootDirs

    def getRootVarDirs(self):
        return self._rootVarDirs
    
    def getRootVarAinstDirs(self):
        return self._rootVarAinstDirs

    def isInRootDir(self, subDir):
        if subDir in self._rootDir:
            return True
        return False

    def isInRootVarDir(self, subDir):
        if subDir in self._rootVarDir:
            return True
        return False

    def isInRootVarAinstDir(self, subDir):
        if subDir in self._rootVarAinstDir:
            return True
        return False

    def isAinstDir(self, dirPath):
        if dirPath == self._root or dirPath == self._getDirPath(self._root):
            return True
        if dirPath in self._rootDirs.values():
            return True
        if dirPath in self._rootVarDirs.values():
            return True
        if dirPath in self._rootVarAinstDirs.values():
            return True
        return False

    def _initRootDirs(self):
        if not self._root:
            return
        for subDir in self._rootDir:
            self._rootDirs[subDir] = self._root + '/' + subDir + '/'
        for subDir in self._rootVarDir:
            self._rootVarDirs[subDir] = self._root + '/var/' + subDir + '/'
        for subDir in self._rootVarAinstDir:
            self._rootVarAinstDirs[subDir] = self._root + '/var/ainst/' + subDir + '/'

    def _getDirPath(self, dirPath):
        if not dirPath:
            return dirPath
        if dirPath[-1] != '/':
            dirPath += '/'
        return dirPath

class AinstRootReader:
    def __init__(self, ainstRoot):
        self._ainstRoot = ainstRoot
        self._filePrefix = 'root-state-'

    def isEffective(self):
        installPkgs = self.getInstallPackages()
        if not installPkgs:
            return False
        return True
    
    def isCurrentStateNumber(self, number):
        numberList = self._getRootStateNumberList()
        if not numberList:
            return False
        return numberList[-1] == number

    def getLatestRootStateByCount(self, count=None):
        stateList = []
        numberList = self._getRootStateNumberList()
        #if count is None, return all the list
        if count is None:
            count = len(numberList)
        if count < 0:
            return stateList
        count = min(count, len(numberList))
        for number in numberList[::-1]:
            if count == 0:
                break
            state = self._getRootStateByNumber(number)
            if state is None:
                continue
            stateList.append((number, state))
            count = count - 1
        return stateList

    def getLatestRootStateByTime(self, timeStamp):
        if timeStamp is None:
            return None
        stateList = []
        numberList = self._getRootStateNumberList()
        for number in numberList[::-1]:
            state = self._getRootStateByNumber(number)
            if state is None:
                continue
            if state.time >= timeStamp:
                stateList.append((number, state))
        return stateList

    def getRootStateByNumber(self, number):
        numberList = self._getRootStateNumberList()
        if not numberList or number not in numberList:
            return None
        return self._getRootStateByNumber(number)

    def getRootStateByTime(self, time):
        numberList = self._getRootStateNumberList()
        if not numberList:
            return None
        lastState = None
        for number in numberList[::-1]:
            lastState = self._getRootStateByNumber(number)
            if lastState.time <= time:
                return lastState
        return lastState

    def getPreviousRootState(self):
        numberList = self._getRootStateNumberList()
        if not numberList or len(numberList) == 1:
            return None
        return self._getRootStateByNumber(numberList[-2])

    def getCurrentRootState(self):
        numberList = self._getRootStateNumberList()
        if not numberList:
            return None
        return self._getRootStateByNumber(numberList[-1])

    def getNextStateFileName(self):
        nextStateNumber = 0
        numberList = self._getRootStateNumberList()
        if numberList:
            nextStateNumber = numberList[-1] + 1
        return self._filePrefix + str(nextStateNumber)

    def isActivePackage(self, pkg):
        activePath = self._ainstRoot.getRootVarAinstDir('active') + pkg.name
        linkPath = file_util.readLink(activePath)
        if linkPath and linkPath.startswith('../packages/'):
            return True
        return False

    def getActivePackages(self):
        'return list [(pkg, pkg-version, mtime)]'
        activePkgs = []
        activeDir = self._ainstRoot.getRootVarAinstDir('active')
        subDirs = file_util.listDir(activeDir)
        if not subDirs:
            return activePkgs
        for subDir in subDirs:
            subDirPath = activeDir + '/' + subDir
            linkPath = file_util.readLink(subDirPath)
            if linkPath and linkPath.startswith('../packages/'):
                packageName = os.path.basename(linkPath)
                mtime = os.lstat(subDirPath).st_mtime
                activePkgs.append((subDir, packageName, mtime))
        return activePkgs

    def getActivePkgMetas(self):
        'return list [(pkg, rpmFilePath, aicfFilePath)]'
        activePkgMetas = []
        activeDir = self._ainstRoot.getRootVarAinstDir('active')
        subDirs = file_util.listDir(activeDir)
        if subDirs is None:
            return None
        for subDir in subDirs:
            subDirPath = activeDir + '/' + subDir
            linkPath = file_util.readLink(subDirPath)
            if linkPath and linkPath.startswith('../packages/'):
                pkgPath = self._ainstRoot.getRootVarAinstDir('packages') +\
                    os.path.basename(linkPath) 
                rpmPath = pkgPath + self._ainstRoot.getBackRpmPath()
                aicfFile = pkgPath + '/ainst/' + subDir + '.aicf'
                activePkgMetas.append((subDir, rpmPath, aicfFile))
        return activePkgMetas

    def getInstallPackages(self):
        installPkgs = []
        installDir = self._ainstRoot.getRootVarAinstDir('packages')
        subDirs = file_util.listDir(installDir)
        if subDirs:
            for subDir in subDirs:
                if file_util.isDir(installDir + subDir):
                    installPkgs.append(subDir)
        return installPkgs

    def getInstallPkgMetas(self):
        'return list [(pkgVer, rpmFilePath)]'
        installPkgMetas = []
        pkgDir = self._ainstRoot.getRootVarAinstDir('packages')
        subDirs = file_util.listDir(pkgDir)
        if subDirs is None:
            return None
        for subDir in subDirs:
            pkgPath = pkgDir + subDir
            if file_util.isDir(pkgPath):
                rpmPath = pkgPath + self._ainstRoot.getBackRpmPath()
                installPkgMetas.append((subDir, rpmPath))
        return installPkgMetas

    def getPkgSettings(self, pkgs=None):
        pkgSettings = {}
        if pkgs is None:
            pkgs = [x for x, y, z in self.getActivePackages()]
        if not pkgs:
            return pkgSettings
        settingsDir = self._ainstRoot.getRootVarAinstDir('settings')
        subDirs = file_util.listDir(settingsDir)
        if not subDirs:
            return pkgSettings
        streamer = SettingStreamer()
        for subDir in subDirs:
            if subDir in pkgs:
                subDirPath = settingsDir + '/' + subDir
                settingMap = streamer.parse(subDirPath)
                if settingMap:
                    pkgSettings[subDir] = settingMap
        return pkgSettings

    def getPkgCrontabs(self):
        pkgCrontabs = {}
        crontabDir = self._ainstRoot.getRootVarDir('cron')
        activeDir = self._ainstRoot.getRootVarAinstDir('active')
        cronFiles = file_util.listDir(crontabDir)
        if not cronFiles:
            return pkgCrontabs
        for cronFile in cronFiles:
            activePath = activeDir + '/' + cronFile
            linkPath = file_util.readLink(activePath)
            if linkPath and linkPath.startswith('../packages/'):
                cronFilePath = crontabDir + '/' + cronFile
                content = file_util.readFromFile(cronFilePath)
                if content:
                    pkgCrontabs[cronFile] = content
        return pkgCrontabs
    
    def getActivePkgFiles(self, pkg):
        if not self.isActivePackage(pkg):
            return None
        pkgFileDbPath = self._ainstRoot.getPkgFileDbPath()
        wrapper = BdbWrapper(pkgFileDbPath)
        if not wrapper.open():
            return None

        files = wrapper.get(pkg.name)
        if files is None:
            return None
        fileList = files.split(self._ainstRoot.getFileSpliter())
        wrapper.close()
        return fileList

    def _getRootStateByNumber(self, number):
        saveDir = self._ainstRoot.getRootVarAinstDir('save')
        currentStateFile = saveDir + self._filePrefix + str(number)
        state = RootStateStreamer().getRootStateFromFile(currentStateFile)
        if not state or state.installRoot != self._ainstRoot.getRoot():
            return None
        return state

    def _getRootStateNumberList(self):
        numberList = []
        saveDir = self._ainstRoot.getRootVarAinstDir('save')
        subDirs = file_util.listDir(saveDir)
        pattern = re.compile(self._filePrefix + '(\d+)')
        if not subDirs:
            return numberList
        for subDir in subDirs:
            match = pattern.match(subDir)
            if match:
                numberList.append(int(match.group(1)))
        numberList.sort()
        return numberList

if __name__ == '__main__':
    ainstRoot = AinstRoot('/home/xiaoming.zhang/xx')
    reader = AinstRootReader(ainstRoot)
    print reader.getInstallPackages()
    print reader.isEffective()
