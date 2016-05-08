#! /usr/bin/python

import rpm
from  package_sack import PackageSackBase
from repository import FakeRepository
from package_object import *
from rpm_header_package import *
from package_util import PackageUtil

class RPMDBPackageSack(PackageSackBase):
    '''
    Represent rpmdb as a packagesack
    '''
    DEP_TABLE = { 
            'requires'  : (rpm.RPMTAG_REQUIRENAME,
                           rpm.RPMTAG_REQUIREVERSION,
                           rpm.RPMTAG_REQUIREFLAGS),
            'provides'  : (rpm.RPMTAG_PROVIDENAME,
                           rpm.RPMTAG_PROVIDEVERSION,
                           rpm.RPMTAG_PROVIDEFLAGS),
            'conflicts' : (rpm.RPMTAG_CONFLICTNAME,
                           rpm.RPMTAG_CONFLICTVERSION,
                           rpm.RPMTAG_CONFLICTFLAGS),
            'obsoletes' : (rpm.RPMTAG_OBSOLETENAME,
                           rpm.RPMTAG_OBSOLETEVERSION,
                           rpm.RPMTAG_OBSOLETEFLAGS)
            }

    def __init__(self, root):
        self.root = root
        self.ts = None
        self._prcoCache = {
            'provides': {}, 
            'requires': {},
            'conflicts': {}, 
            'obsoletes': {}
            }
        self._provideCache = {}
        self._requireCache = {}
        self._conflictCache = {}
        self._idx2PkgDict = {}
        self._name2PkgDict = {}
        self._tuple2PkgDict = {}
        self._completelyLoaded = False

        self._repo = FakeRepository('/', installed=True)
        self._repo.setPackageSack(self)

    def addPackageObject(self, pkg):
        pass

    def deletePackageObject(self, pkg):
        pass

    def returnPackages(self):
        pass

    def getRequires(self, require):
        name, version  = require.name, require.version
        if require in self._requireCache:
            return self._requireCache[require]

        pkgs = self.searchPkgByRequire(name)
        result = {}
        for pkgObj in pkgs:
            if name[0] == '/' and version is None:
                result[pkgObj] = [Require(name, None, None, None, None)]
                continue
            requires = PackageUtil.matchingRequire(pkgObj, require)
            if requires:
                result[pkgObj] = requires
        self._requireCache[require] = result
        return result

    def getProvides(self, provide):
        name, version = provide.name, provide.version
        if provide in self._provideCache:
            return self._provideCache[provide]

        pkgs = self.searchPkgByProvide(name)
        result = {}
        for pkgObj in pkgs:
            if name[0] == '/' and version is None:
                result[pkgObj] = [Provide(name, None, None, None, None)]
            provides = PackageUtil.matchingProvide(pkgObj, provide)
            if provides:
                result[pkgObj] = provides
        self._provideCache[provide] = result
        return result

    def getConflicts(self, conflict):
        name, version = conflict.name, conflict.version
        if conflict in self._conflictCache:
            return self._conflictCache[conflict]

        pkgs = self.searchPkgByConflict(name)
        result = {}
        for pkgObj in pkgs:
            conflicts = PackageUtil.matchingProvide(pkgObj, conflict)
            if conflicts:
                result[pkgObj] = conflicts
        self._conflictCache[conflict] = result
        return result

    def getPkgs(self):
        return self.searchPkg()

    def searchPkg(self, name=None, epoch=None, version=None,
                  release=None, arch=None):
        pkgTuple = (name, arch, epoch, version, release)
        if self._tuple2PkgDict.has_key(pkgTuple):
            return self._tuple2PkgDict[pkgTuple]
        
        loc = locals()
        ret = []

        if self._completelyLoaded:
            if name is not None:
                pkgs = self._name2PkgDict.get(name, [])
            else:
                return self._name2PkgDict.values()
            for po in pkgs:
                for tag in ('name', 'epoch', 'version', 'release', 'arch'):
                    if loc[tag] is not None and loc[tag] != getattr(po, tag):
                        break
                else:
                    ret.append(po)
            return ret

        ts = self._getTs()
        if name is not None:
            mi = ts.dbMatch('name', name)
        elif arch is not None:
            mi = ts.dbMatch('arch', arch)
        else:
            mi = ts.dbMatch()
            self._completelyLoaded = True

        for hdr in mi:
            po = self._makePackageObject(hdr, mi.instance())
            for tag in ('name', 'epoch', 'version', 'release', 'arch'):
                if loc[tag] is not None and loc[tag] != getattr(po, tag):
                    break
            else:
                ret.append(po)
        return ret

    def searchPkgByName(self, name):
        return self.searchPkg(name)

    def searchPkgByProvide(self, name):
        return self.searchPrco(name, 'provides')

    def searchPkgByRequire(self, name):
        return self.searchPrco(name, 'requires')

    def searchPkgByConflict(self, name):
        return self.searchPrco(name, 'conflicts')

    def searchPkgByObsolete(self, name):
        return self.searchPrco(name, 'obsoletes')

    def searchPkgByFile(self, name):
        ts = self._getTs()
        result = {}
        mi = ts.dbMatch('basenames', name)
        for hdr in mi:
            pkg = self._makePackageObject(hdr, mi.instance())
            if not result.has_key(pkg.pkgid):
                result[pkg.pkgid] = pkg
        del mi

        result = result.values()
        return result

    def searchPrco(self, name, prcotype):
        result = self._prcoCache[prcotype].get(name)
        if result is not None:
            return result
        ts = self._getTs()
        result = {}
        tag = self.DEP_TABLE[prcotype][0]
        mi = ts.dbMatch(tag, name)
        for hdr in mi:
            po = self._makePackageObject(hdr, mi.instance())
            result[po.pkgid] = po
        del mi

        if prcotype == 'provides' and name[0] == '/':
            fileResults = self.searchPkgByFile(name)
            for pkg in fileResults:
                result[pkg.pkgid] = pkg
        result = result.values()
        self._prcoCache[prcotype][name] = result
        return result

    def _getTs(self):
        if self.ts:
            return self.ts
        self.ts = rpm.TransactionSet()
        self.ts.setVSFlags((rpm._RPMVSF_NOSIGNATURES|rpm._RPMVSF_NODIGESTS))
        return self.ts

    def _makePackageObject(self, hdr, index):
        if self._idx2PkgDict.has_key(index):
            return self._idx2PkgDict[index]
        po = InstalledRpmPackage(hdr, self._repo)
        self._idx2PkgDict[index] = po
        self._name2PkgDict.setdefault(po.name, []).append(po)
        self._tuple2PkgDict[po.getTuple()] = po
        return po


if __name__ == '__main__':
    from package_object import Require, Provide, Conflict
    import time
    start = time.time()
    pkgSack = RPMDBPackageSack('/')
    lst = pkgSack.searchPrco('anet', 'provides')
    #print lst
    #print lst[0].toString()
    lst = pkgSack.searchPkgByFile('/usr/local/lib64/libanet.so')
    #print lst
    #print lst[0].toString()
    result = pkgSack.getRequires(Require(name = 'alog'))
    #print result
    result = pkgSack.getProvides(Provide(name = 'alog'))
    #print result
    result = pkgSack.getConflicts(Conflict(name='ttfonts-ja'))
    #print result
    end = time.time()
    print 'init rpmdb sack cost: ', end - start

    print pkgSack.searchPkg()
