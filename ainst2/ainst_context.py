#! /usr/bin/python

from logger import Log
import rpmutils
import file_util
from repository import Repository
from rpm_header_package import LocalRpmPackage
from repo_storage import RepoStorage
from yum_repository import YumRepository
from rpmdb_package_sack import RPMDBPackageSack
from package_sack import MultiPackageSack, PackageSack
from package_object import FakeAinstLocalInstallPackage
from ainst_package_sack_builder import AinstPackageSackBuilder

class AinstContext:
    def getByProvide(self, provide):
        return {}

    def getByRequire(self, require):
        return {}

    def getByConflict(self, conflict):
        return {}

    def getByName(self, name):
        return {}

    def setPrefixFilter(self, prefixFilter):
        return

class AinstMultiRootContext(AinstContext):
    def __init__(self, rootSack, localSack, repoSack):
        self._rootSack = rootSack
        self._localSack = localSack
        self._repoSack = repoSack
        self._getPkgsCache = None

    def getPkgs(self):
        if self._getPkgsCache is not None:
            return self._getPkgsCache
        self._getPkgsCache = {}
        if self._rootSack:
            self._getPkgsCache.update({'/':self._rootSack.getPkgs()})
        if self._localSack:
            self._getPkgsCache.update(self._localSack.getPkgs())
        if self._repoSack:
            self._getPkgsCache.update(self._repoSack.getPkgs())
        return self._getPkgsCache

    def searchPkgs(self, pkg):
        if not pkg:
            return None
        name, ver, rel, epoch, arch = rpmutils.splitPkgName3(pkg)
        repo2Pkgs = {}
        if self._rootSack:
            pkgs = self._rootSack.searchPkg(name, epoch, ver, rel, arch)
            repo2Pkgs.update({'/' : pkgs})
        if self._localSack:
            repo2Pkgs.update(self._localSack.searchPkg2(name, epoch, ver, rel, arch))
        if self._repoSack:
            repo2Pkgs.update(self._repoSack.searchPkg2(name, epoch, ver, rel, arch))
        return repo2Pkgs

    def searchInstallRootPkgs(self, name=None, epoch=None, ver=None,
                              rel=None, arch=None):
        result = []
        if self._rootSack:
            pkgs = self._rootSack.searchPkg(name, epoch, ver, rel, arch)
            result.extend(pkgs)
        if self._localSack:
            repo2Pkgs = self._localSack.searchPkg2(name, epoch, ver, rel, arch)
            for value in repo2Pkgs.values():
                result.extend(value)
        return result

class AinstContextImpl(AinstContext):
    def __init__(self, installRoot, repoSack, rootSack, localSacks):
        self._installRoot = installRoot
        self._repoSack = repoSack
        self._rootSack = rootSack
        self._localSacks = localSacks
        self._provideCache = {}
        self._requireCache = {}
        self._conflictCache = {}
        self._nameCache = {}
        self._prefixFilter = ''

    def setPrefixFilter(self, prefixFilter):
        self._prefixFilter = prefixFilter
        
    def isRootInstall(self):
        return self._installRoot == '/'

    def getInstallRoot(self):
        return self._installRoot

    def getByProvide(self, provide):
        if self._provideCache.has_key(provide):
            return self._provideCache[provide]
        result = {}
        if self._repoSack:
            result.update(self._repoSack.getProvides(provide))
        if self._rootSack:
            rootPrvs = self._rootSack.getProvides(provide)
            for p in rootPrvs.keys():
                if (not self.isRootInstall() and self._prefixFilter != '' and
                    self._prefixFilter in p.prefixes):
                    del(rootPrvs[p])
            result.update(rootPrvs)
        #if not self.isRootInstall():
        if self._localSacks:
            result.update(self._localSacks.getProvides(provide))
        self._provideCache[provide] = result
        return result

    def getByRequire(self, require):
        if self._requireCache.has_key(require):
            return self._requireCache[require]
        result = {}
        if self._repoSack:
            result.update(self._repoSack.getRequires(require))
        if self._localSacks:
            result.update(self._localSacks.getRequires(require))
        if self.isRootInstall() and self._rootSack:
            result.update(self._rootSack.getRequires(require))
        self._requireCache[require] = result
        return result

    def getByConflict(self, conflict):
        if self._conflictCache.has_key(conflict):
            return self._conflictCache[conflict]
        result = {}
        if self._repoSack:
            result.update(self._repoSack.getConflicts(conflict))
        if not self.isRootInstall():
            if self._localSacks:
                result.update(self._localSacks.getConflicts(conflict))
        elif self.isRootInstall() and self._rootSack:
            result.update(self._rootSack.getConflicts(conflict))
        self._conflictCache[conflict] = result
        return result

    def getByName(self, name):
        if self._nameCache.has_key(name):
            return self._nameCache[name]
        result = []
        if self._repoSack:
            result.extend(self._repoSack.searchPkgByName(name))
        if self._localSacks:
            result.extend(self._localSacks.searchPkgByName(name))
        if self._rootSack:
            result.extend(self._rootSack.searchPkgByName(name))
        self._nameCache[name] = result
        return result

    def searchInstallRootPkgs(self, name=None, epoch=None, version=None,
                              release=None, arch=None):
        pkgs = []
        if self.isRootInstall() and self._rootSack:
            pkgs.extend(self._rootSack.searchPkg(name, epoch, version,
                                                 release, arch))
        elif self._localSacks:
            pkgs.extend(self._localSacks.searchPkg(name, epoch, version,
                                                   release, arch))
        return pkgs

    def searchInstalledPkgs(self, name=None, epoch=None, version=None,
                            release=None, arch=None):
        pkgs = []
        if not self.isRootInstall():
            if self._localSacks:
                pkgs.extend(self._localSacks.searchPkg(name, epoch, version,
                                                       release, arch))
        if self._rootSack:
            pkgs.extend(self._rootSack.searchPkg(name, epoch, version,
                                                 release, arch))
        return pkgs

    def searchAvailablePkgs(self, name=None, epoch=None, version=None,
                            release=None, arch=None):
        if self._repoSack:
            return self._repoSack.searchPkg(name, epoch, version,
                                            release, arch)
        return []

class SimpleAinstContextImpl(AinstContext):
    def __init__(self, installRoot):
        self.packageSack = None
        self.installRoot = installRoot

    def isRootInstall(self):
        return self.installRoot == '/'

    def getInstallRoot(self):
        return self.installRoot

    def getByProvide(self, provide):
        return self.packageSack.getProvides(provide)

    def getByRequire(self, require):
        return self.packageSack.getRequires(require)

    def getByConflict(self, conflict):
        return self.packageSack.getConflicts(conflict)

    def getByName(self, name):
        return self.packageSack.searchPkgByName(name)

class AinstContextBuilder:
    def __init__(self):
        '# < / for repo cmp'
        self.installRootRepoPrefix = '#'

    def buildLocalRemoveContext(self, installRoot):
        if installRoot == '/':
            return None
        builder = AinstPackageSackBuilder(installRoot)
        sack = builder.buildInstalledPkgSack()
        if sack is None:
            Log.cout(Log.DEBUG, 'Build install pkg sack of %s failed' % installRoot)
            return None
        rootSack = RPMDBPackageSack('/')
        return AinstContextImpl(installRoot, None, rootSack, sack)

    def buildMultiRootContext(self, installRoots, ainstConf, useRepo=False, repos=[]):
        repoSack = None
        if useRepo:
            repoSack = self._initRepos(ainstConf, repos)
            if repoSack is None:
                return None

        rootSack = None
        localSack = MultiPackageSack()
        for installRoot in installRoots:
            if installRoot == '/':
                rootSack = RPMDBPackageSack('/')
            else:
                sack = AinstPackageSackBuilder(installRoot).buildActivePkgSack()
                if sack is None:
                    Log.cout(Log.DEBUG, 'Build active pkg sack of %s failed' % installRoot)
                    continue
                localSack.addPackageSack(installRoot, sack)                
        return AinstMultiRootContext(rootSack, localSack, repoSack)

    def buildAinstContext(self, installRoot, ainstConf, useRepo=True,
                          repos=[], localRepos=[], localRoots=None,
                          localActivePkgs=None, localDeactivePkgs=None):
        repoSack = None
        if useRepo:
            repoSack = self._initRepos(ainstConf, repos)
            self._initLocalRepos(repoSack, localRepos)
            self._initInstallRootRepos(repoSack, installRoot)
            if repoSack is None:
                return None

        rootSack = RPMDBPackageSack('/')
        localSacks = MultiPackageSack()
        if installRoot == '/':
            if localRoots:
                for localRoot in localRoots:
                    builder = AinstPackageSackBuilder(localRoot)
                    sack = builder.buildActivePkgSack()
                    if sack is None:
                        Log.cout(Log.DEBUG, 'Build active pkg sack of %s failed' % localRoot)
                        continue
                    localSacks.addPackageSack(localRoot, sack)
        else:
            builder = AinstPackageSackBuilder(installRoot)
            sack = builder.buildActivePkgSack()
            if sack is None:
                Log.cout(Log.DEBUG, 'Build active pkg sack of %s failed' % installRoot)
            else:
                localSacks.addPackageSack(installRoot, sack)
            self._addFakeLocalInstallPkgs(localActivePkgs, installRoot, localSacks)
            if not self._removeWillDeactivePkgs(localSacks, localDeactivePkgs):
                return None
        return AinstContextImpl(installRoot, repoSack, rootSack, localSacks)

    def _removeWillDeactivePkgs(self, localSacks, localDeactivePkgs):
        if not localDeactivePkgs or not localSacks:
            return True
        for pkg in localDeactivePkgs:
            result = localSacks.searchPkg(pkg.name, pkg.epoch, pkg.version,
                                          pkg.release, pkg.arch)
            if not result:
                continue
            if len(result) > 1:
                return False
            localSacks.deletePackageObject(result[0])
        return True

    def _addFakeLocalInstallPkgs(self, localActivePkgs, installRoot, sack):
        if localActivePkgs:
            for pkg in localActivePkgs:
                package = FakeAinstLocalInstallPackage(Repository(installRoot), pkg)
                sack.addPackageObject(package)
        return True

    def _initInstallRootRepos(self, repoSack, installRoot):
        if installRoot == '/':
            return True
        builder = AinstPackageSackBuilder(installRoot)
        sack = builder.buildInstalledPkgRepoSack()
        if sack is None:
            Log.cout(Log.DEBUG, 'Build install pkg sack of %s failed' % installRoot)
            return False
        repoSack.addPackageSack(self.installRootRepoPrefix + installRoot, sack)
        return True

    def _initLocalRepos(self, repoSack, localRepos):
        if not localRepos:
            return True
        if not repoSack:
            repoSack = MultiPackageSack()
        for local in localRepos:
            fileNames = file_util.listDir(local)
            if not fileNames:
                continue
            pkgSack = PackageSack()
            for name in fileNames:
                path = local + '/' + name
                pkg = LocalRpmPackage(path)
                if pkg.init():
                    pkgSack.addPackageObject(pkg)
            repoSack.addPackageSack(local, pkgSack)
        return True

    def _initRepos(self, ainstConf, repos):
        if not ainstConf:
            Log.cout(Log.ERROR, 'Ainst config is None')
            return None
        repoStorage = self._initRepoStorage(ainstConf)
        if not repoStorage:
            Log.cout(Log.ERROR, 'Repo storage init failed')
            return None
        repoStorage.processDisableEnable(repos)
        return repoStorage.getPackageSack()

    def _initRepoStorage(self, ainstConf):
        if not ainstConf or len(ainstConf.repoConfigItems) == 0:
            return None
        repoStorage = RepoStorage()
        for repoid, item in ainstConf.repoConfigItems.iteritems():
            yumRepo = YumRepository(repoid, item, ainstConf.maxfilelength,
                                    ainstConf.retrytime, ainstConf.sockettimeout)
            yumRepo.cachedir = ainstConf.cachedir
            yumRepo.expireTime = ainstConf.expiretime
            repoStorage.addRepo(yumRepo)
        return repoStorage
