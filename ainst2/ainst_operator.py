#! /usr/bin/python

import os
import rpmutils
import file_util
import common
from logger import Log
from repo_storage import RepoStorage
from yum_repository import YumRepository
from resolver import PackageArchSorter

class OperatorRet:
    OPERATE_SUCCESS = 0
    OPERATE_FAILED = 1
    OPERATE_NOT_SUPPORT = 2

class AinstOperator:
    def __init__(self, ainstConf):
        self._ainstConf = ainstConf
        self._locked = False
        self._lockFp = None

    def lock(self):
        if self._locked:
            return True

        ainstLock = self._ainstConf.ainstroot + '/ainst.lock'
        preUmask = os.umask(0)
        self._lockFp = file_util.getFp(ainstLock, 'a')
        os.umask(preUmask)
        if not self._lockFp:
            print 'lock fp failed'
            return False
        self._locked = file_util.lockFp(self._lockFp)
        return self._locked

    def unlock(self):
        if not self._locked:
            return True

        if file_util.unlockFp(self._lockFp):
            self._lockFp.close()
            self._locked = False
            return True
        return False

    def makeCache(self, cacheParam):
        repoStorage = self._getRepoStorage(self._ainstConf, cacheParam.repos)
        if repoStorage is None:
            Log.cout(Log.ERROR, 'Get repo storage failed')
            return OperatorRet.OPERATE_FAILED
        if not repoStorage.makeCache():
            Log.cout(Log.ERROR, 'RepoStorage makeCache failed')
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def clearCache(self, cacheParam):
        if cacheParam.clearAll:
            return self._clearAllCache(cacheParam)
        repoStorage = self._getRepoStorage(self._ainstConf, cacheParam.repos)
        if repoStorage is None:
            Log.cout(Log.ERROR, 'Get repo storage failed')
            return OperatorRet.OPERATE_FAILED
        if not repoStorage.clearCache():
            Log.cout(Log.ERROR, 'RepoStorage clearCache failed')
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS            

    def _clearAllCache(self, cacheParam):
        if not file_util.remove(self._ainstConf.cachedir):
            Log.cout(Log.ERROR, 'clearAllCache failed')
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS
    
    def _getRepoStorage(self, ainstConf, repos):
        if not ainstConf or len(ainstConf.repoConfigItems) == 0:
            Log.cout(Log.ERROR, 'Ainst config is invalid')
            return None
        repoStorage = RepoStorage()
        for repoid, item in ainstConf.repoConfigItems.iteritems():
            yumRepo = YumRepository(repoid, item, ainstConf.maxfilelength,
                                    ainstConf.retrytime, ainstConf.sockettimeout)
            yumRepo.cachedir = ainstConf.cachedir
            yumRepo.expireTime = ainstConf.expiretime
            repoStorage.addRepo(yumRepo)
        repoStorage.processDisableEnable(repos)
        return repoStorage

    def _selectInstallPkgs(self, context, pkgs):
        installPkgs = []
        for pkg in pkgs:
            installPkg = self._selectPkg(context, pkg)
            if installPkg == None:
                Log.cout(Log.ERROR, 'No packages %s available. Abort Installation.' % pkg)
                return None
            installPkgs.append(installPkg)
        return installPkgs
    
    def _selectPkg(self, context, pkg):
        pkgs = []
        name, ver, rel, epoch, arch = rpmutils.splitPkgName3(pkg)
        installRootPkgs = context.searchInstallRootPkgs(name, epoch, ver, rel, arch)
        if installRootPkgs:
            pkgs.extend(installRootPkgs)
        availablePkgs = context.searchAvailablePkgs(name, epoch, ver, rel, arch)

        if availablePkgs:
            pkgs.extend(availablePkgs)
        if not pkgs:
            return None
        sorter = PackageArchSorter(arch)
        pkgs = sorter.sort(pkgs)
        return pkgs[0]

    def _selectInstalledPkgs(self, context, pkgs):
        removePkgs = []
        for pkg in pkgs:
            name, ver, rel, epoch, arch = rpmutils.splitPkgName3(pkg)
            installRootpkgs = context.searchInstallRootPkgs(name, epoch, ver,
                                                            rel, arch)
            if not installRootpkgs:
                Log.cout(Log.WARNING, 'No installed [%s] in installRoot' % pkg)
                continue
            if len(installRootpkgs) > 1:
                Log.cout(Log.ERROR, 'Too many package: [%s] is installed' % pkg)
                return None
            removePkgs.append(installRootpkgs[0])
        return removePkgs

    def _printPkgInfo(self, pkg, param, indents):
        if param.requires:
            Log.cout(Log.INFO, " " * indents + "Requires: ")
            for require in pkg.requires:
                Log.cout(Log.INFO, " " * indents * 2 + "%s" % require)
        if param.provides:
            Log.cout(Log.INFO, " " * indents + "Provides: ")
            for provide in pkg.provides:
                Log.cout(Log.INFO, " " * indents * 2 + "%s" % provide)
        if param.conflicts:
            Log.cout(Log.INFO, " " * indents + "Conflicts: ")
            for conflict in pkg.conflicts:
                Log.cout(Log.INFO, " " * indents * 2 + "%s" % conflict)
        if param.obsoletes:
            Log.cout(Log.INFO, " " * indents + "Obsoletes: ")
            for obsolete in pkg.obsoletes:
                Log.cout(Log.INFO, " " * indents * 2 + "%s" % obsolete)

    def activate(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def install(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def deactivate(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def remove(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def start(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def stop(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def restart(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def reload(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def save(self, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def restore(self, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def set(self, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def list(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def history(self, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

    def crontab(self, pkgs, param, command):
        return OperatorRet.OPERATE_NOT_SUPPORT

if __name__ == '__main__':
    pass
