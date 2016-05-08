#! /usr/bin/python

import os
from logger import Log
import rpmutils
import file_util
from cache_handler import RepoCacheHandler
from ainst_root import AinstRoot, AinstRootReader
from root_executor import RootExecutor
from package_util import PackageUtil

class RootInstallExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryrun=False):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        self._pkg = pkg
        self._init()
        self._dryrun = dryrun

    def _init(self):
        self._executed = False
        self._rootInitTrace = None
        self._ainstPkgDir = None
        self._ainstTmpPkgDir = None
        self._success = False
        
    def execute(self):
        Log.cout(Log.INFO, 'Install pkg %s ...' % self._pkg)
        if self._dryrun:
            return True

        if self._executed:
            Log.cout(Log.DEBUG, 'Install %s has always executed' % self._pkg)
            return False
        self._executed = True

        ret, self._rootInitTrace = self._ainstRoot.init()
        if not ret:
            Log.cout(Log.ERROR, 'Init ainst root failed')
            return False

        if not self._ainstRoot.checkRoot():
            Log.cout(Log.ERROR, 'Check ainst root failed')
            return False

        pkgDirName = PackageUtil.getPkgNameVersion(self._pkg)
        if not pkgDirName:
            Log.cout(Log.ERROR, 'Get pkg %s dir name failed' % self._pkg)
            return False

        self._ainstPkgDir = self._ainstRoot.getRootVarAinstDir('packages') + pkgDirName
        if file_util.isDir(self._ainstPkgDir):
            Log.cout(Log.INFO, 'Package %s is always installed' % self._pkg)
            return True

        self._ainstTmpPkgDir = self._ainstRoot.getRootVarAinstDir('tmp') + pkgDirName
        if not self._installInTmpDir(self._pkg, self._ainstTmpPkgDir):
            Log.cout(Log.ERROR, 'Install pkg %s to tmp dir failed' % pkgDirName)
            self.undo()
            return False

        if not file_util.move(self._ainstTmpPkgDir, self._ainstPkgDir):
            Log.cout(Log.ERROR, 'Move pkg %s to packages dir failed' % self._pkg)
            self.undo()
            return False

        self._success = True
        Log.cout(Log.DEBUG, 'Install pkg %s success' % self._pkg)
        return True

    def undo(self):
        if self._dryrun:
            return True

        if not self._executed:
            return False

        Log.cout(Log.INFO, 'Undo install pkg %s ...' % self._pkg)
        if self._success:
            if not file_util.remove(self._ainstPkgDir):
                Log.cout(Log.ERROR, 'Remove pkg %s packages dir failed' % self._pkg)
                return False
            if self._rootInitTrace:
                self._ainstRoot.clearInit(self._rootInitTrace)
            self._init()
            return True

        if self._ainstTmpPkgDir:
            if not file_util.remove(self._ainstTmpPkgDir):
                Log.cout(Log.ERROR, 'Remove pkg %s tmp dir failed' % self._pkg)
                return False
        
        if self._rootInitTrace:
            self._ainstRoot.clearInit(self._rootInitTrace)

        self._init()
        return True

    def _installInTmpDir(self, pkg, ainstTmpPkgDir):
        rpmFilePath = self._getRpmFilePath(pkg)
        if not rpmFilePath:
            return False

        if not file_util.makeDir(ainstTmpPkgDir, True):
            Log.cout(Log.ERROR, 'Prepare tmp dir for install failed')
            return False

        if not rpmutils.rpm2dir(rpmFilePath, ainstTmpPkgDir):
            Log.cout(Log.ERROR, 'Rpm %s to dir failed' % rpmFilePath)
            return False

        # disable dir checking
        # if not self._changeToValidRootDir(ainstTmpPkgDir):
        #     Log.cout(Log.ERROR, 'Change to valid root dir failed')
        #     return False

        if not file_util.makeDir(ainstTmpPkgDir + '/ainst'):
            return False
        if not file_util.copyFile(rpmFilePath,
                                  ainstTmpPkgDir + self._bakRpmPath):
            Log.cout(Log.ERROR, 'Copy installed.rpm failed')
            return False
        return True

    def _getRpmFilePath(self, pkg):
        location = pkg.getLocation()
        if not location:
            return None
        rpmFilePath = location
        if location.lower().startswith('http'):
            cacheHandler = RepoCacheHandler(pkg.repo.id, None, 
                                            self._ainstConf.cachedir, 
                                            self._ainstConf.expiretime,
                                            self._ainstConf.maxfilelength,
                                            self._ainstConf.retrytime,
                                            self._ainstConf.sockettimeout)
            rpmFilePath = cacheHandler.getPackage(pkg)
            if rpmFilePath is None:
                Log.cout(Log.ERROR, 'Get Package %s failed' % pkg)
        return rpmFilePath

    # disable dir checking
    # def _changeToValidRootDir(self, dirPath):
    #     ret, prefixList = self._getValidPrefix(dirPath)
    #     if not ret:
    #         Log.cout(Log.ERROR, 'Dir %s has invalid prefix' % dirPath)
    #         return False

    #     return self._dropPrefix(dirPath, prefixList)

    # def _isValidPath(self, path):
    #     name = os.path.basename(path)
    #     if file_util.isDir(path):
    #         if not self._ainstRoot.isInRootDir(name) and name != 'ainst':
    #             return False
    #     return True
        
    # def _dropPrefix(self, dirPath, prefixList):
    #     if not prefixList:
    #         return True
    #     prefix = '/'
    #     for pre in prefixList:
    #         prefix += pre + '/'
    #     if not file_util.moveAllSubDir(dirPath + prefix, dirPath):
    #         return False
    #     return file_util.remove(dirPath + '/' + prefixList[0])

    # def _getValidPrefix(self, dirPath):
    #     dirs = file_util.listDir(dirPath)
    #     if not dirs:
    #         Log.cout(Log.ERROR, 'Dir %s is invalid' % dirPath)
    #         return False, None

    #     for path in dirs:
    #         if not self._isValidPath(dirPath + '/' + path):
    #             return False, None
    #     return True, None

