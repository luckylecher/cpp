#! /usr/bin/python

import os
from logger import Log
import rpmutils
import file_util
from package_util import PackageUtil
from aicf import AicfParser
from aicf_info_wrapper import AicfInfoWrapper
from ainst_root import AinstRoot, AinstRootReader
from root_executor import RootExecutor
from root_deactivate_executor import RootDeactivateExecutor
from root_install_executor import RootInstallExecutor

class RootRemoveExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf, pkg, dryrun=False):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        self._pkg = pkg
        self._pkgTmpSuffix = '.packages.tmp'
        self._settingTmpSuffix = '.settings.tmp'
        self._tmpPkgPath = None
        self._tmpSettingPath = None
        self._dryrun = dryrun
        self._init()

    def _init(self):
        self._executed = False
        self._tmpPkgPath = None
        self._tmpSettingPath = None

    def execute(self):
        Log.cout(Log.INFO, 'Remove pkg %s ...' % self._pkg)
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

        self._ainstPkgDir = self._ainstRoot.getRootVarAinstDir('packages') + pkgDirName
        self._settingPath = self._ainstRoot.getRootVarAinstDir('settings') + self._pkg.name

        if not self._removeSettings():
            Log.cout(Log.ERROR, 'Remove setting of pkg %s failed' % self._pkg.name)
            self.undo()
            return False

        if not self._removePkgDir(pkgDirName):
            Log.cout(Log.ERROR, 'Remove packages dir of %s failed' % self._pkg)
            self.undo()
            return False

        Log.cout(Log.DEBUG, 'Remove pkg %s success' % self._pkg)
        return True

    def undo(self):
        if self._dryrun:
            return True
        if not self._executed:
            return False
        
        Log.cout(Log.INFO, 'Undo remove pkg %s ...' % self._pkg)
        if not self._recoverPkgDir() or not self._recoverSettings():
            return False

        self._init()
        return True

    def _removePkgDir(self, pkgDirName):
        if not file_util.isDir(self._ainstPkgDir):
            return True

        tmpPkgPath = self._ainstRoot.getRootVarAinstDir('tmp') +\
            pkgDirName + self._pkgTmpSuffix
        if not file_util.remove(tmpPkgPath) or\
                not file_util.move(self._ainstPkgDir, tmpPkgPath):
            return False
        self._tmpPkgPath = tmpPkgPath
        return True

    def _recoverPkgDir(self):
        if not self._tmpPkgPath:
            return True
        if not file_util.isDir(self._tmpPkgPath) or\
                not file_util.move(self._tmpPkgPath, self._ainstPkgDir):
            return False
        return True

    def _removeSettings(self):
        if not file_util.isFile(self._settingPath):
            return True
        tmpPath = self._ainstRoot.getRootVarAinstDir('tmp') +\
            self._pkg.name + self._settingTmpSuffix
        if not file_util.remove(tmpPath) or\
                not file_util.move(self._settingPath, tmpPath):
            return False
        self._tmpSettingPath = tmpPath
        return True

    def _recoverSettings(self):
        if not self._tmpSettingPath:
            return True
        if not file_util.isFile(self._tmpSettingPath) or\
                not file_util.move(self._tmpSettingPath, self._settingPath):
            return False
        return True
        

if __name__ == '__main__':
    installRoot = '/home/xiaoming.zhang/xx/'
    ainstRoot = AinstRoot(installRoot)
    ainstRoot.init()
    rpmPath = '/home/xiaoming.zhang/aicf/aggregator/build/release64/bin_rpm/RPMS/x86_64/aggregator-9.9.1-rc_1.x86_64.rpm'
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
    package.version = '9.9.1'
    package.release = 'rc_1'
    package.epoch = '0'
    package.arch = 'x86_64'
    
    executor = RootRemoveExecutor(ainstRoot, package)
    print executor.execute()
    import time
    time.sleep(10)
    print executor.undo()
