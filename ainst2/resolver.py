#! /usr/bin/python

import error
import rpmutils
import arch
from package_object import *
from logger import Log

#const variable
INSTALL = 0
REMOVE = 1
CHECK = 2

def comparePoEVR(po1, po2):
    """
    Compare two Package or PackageEVR objects.
    """
    (e1, v1, r1) = (po1.epoch, po1.version, po1.release)
    (e2, v2, r2) = (po2.epoch, po2.version, po2.release)
    return rpmutils.compareEVR((e1, v1, r1), (e2, v2, r2))

class Transaction:
    '''class represent the operations need to do'''
    def __init__(self, context):
        self._context = context
        self._operations = {}

    def getContext(self):
        return self._context

    def getOperation(self, pkg):
        if self._operations.has_key(pkg):
            return self._operations.get(pkg)
        return None

    def setOperation(self, pkg, operation):
        op = self.getOperation(pkg)
        if op == operation:
            return

        if operation is INSTALL:
            if not pkg.installed():
                self._operations[pkg] = INSTALL
            elif pkg in self._operations:
                del self._operations[pkg]
            
        if operation is REMOVE:
            if pkg.installed():
                self._operations[pkg] = REMOVE
            elif pkg in self._operations:
                del self._operations[pkg]
        return

    def delOperation(self, pkg):
        if pkg in self._operations:
            del self._operations[pkg]

    def getOperations(self):
        return self._operations

    def installed(self, pkg):
        op = self.getOperation(pkg)
        return op == INSTALL or (pkg.installed() and op != REMOVE)

    def removed(self, pkg):
        op = self.getOperation(pkg)
        return op == REMOVE or (not pkg.installed() and op != INSTALL)
    
    def clear(self):
        self._context = None
        self._operations = {}

    def copy(self):
        trans = Transaction(self._context)
        trans._operations = {}
        trans._operations.update(self._operations)
        return trans

    def assign(self, trans):
        self._context = trans._context
        self._operations = {}
        self._operations.update(trans._operations)

    def getByProvide(self, provide):
        return self._context.getByProvide(provide)

    def getByRequire(self, require):
        return self._context.getByRequire(require)

    def getByConflict(self, conflict):
        return self._context.getByConflict(conflict)

    def getByName(self, name):
        return self._context.getByName(name)

    def __str__(self):
        return str(self._operations)

class _Excludes:
    '''define class for exclude pkg
       may be we need a log of packages with some feature.
    '''
    def __init__(self):
        self._excludes = {}

    def exclude(self, pkg):
        self._excludes[pkg] = True

    def unexclude(self, pkg):
        if pkg in self._excludes:
            del self._excludes[pkg]

    def excluded(self, pkg):
        return self._excludes.has_key(pkg)

    def copy(self):
        excludes = _Excludes()
        excludes._excludes.update(self._excludes)
        return excludes

    def assign(self, excludes):
        self._excludes = {}
        self._excludes.update(excludes._excludes)

    def clear(self):
        self._excludes = {}

class PackageSorter:
    """base class to sort packages"""
    def sort(self, pkgs):
        pass

class PackageArchSorter(PackageSorter):
    def __init__(self, compareArch):
        self._arch = compareArch

    def sort(self, pkgs):
        """
        sort pkg with (arch, (epoch, version, release), repoid)
        """
        if self._arch is None:
            self._arch = arch.getBestArch()
        pkgs = sorted(pkgs, lambda x, y: self._comparePkg(x, y, self._arch))
        return pkgs

    def _comparePkg(self, x, y, compareArch):
        ret = self._compareProvider(x, y, compareArch)
        if ret == 0:
            ret = self._compareRepo(x, y)
        return ret

    def _compareProvider(self, x, y, compareArch):
        """
        For compareArch, if x is more compatable return < 0
        equally compatable return 0, otherwise return > 0
        """
        ret = arch.compareArchDistance(x, y, compareArch)
        if x == ret:
            return -1
        elif y == ret:
            return 1
        ret = cmp(y.name, x.name)
        if ret != 0:
            return ret
        return comparePoEVR(y, x)

    def _compareRepo(self, x, y):
        """
        Firstly, installed repo is prior
        If both installed, /home/** > /
        If both not installled /home/** > repo
        """
        if x.repo.installed() == y.repo.installed():
            if x.repo.installed():
                return cmp(y.repo.id, x.repo.id)
            return cmp(x.repo.id, y.repo.id)
        if x.repo.installed():
            return -1
        if y.repo.installed():
            return 1

class PackageFilter:
    def filter(self, pkgs):
        return pkgs

class PackageArchFilter(PackageFilter):
    """Filter pkg which is not compatable for compareArch"""
    def __init__(self, arch):
        self.setArch(arch)

    def filter(self, pkgs):
        compatArchList = arch.getCompatibleArchList(self._arch)
        return [x for x in pkgs if x.arch in compatArchList]

    def setArch(self, arch):
        self._arch = arch

class ResolverOption:
    """
    Config option for resolver
    upgrade:       whether can not upgrade installed package
    downgrade:     whether it can install old version of installed package
    exclusiveDeps: whether if deps of one package is mutually exclusive 
                   of installed package, it will resolve failed
    """
    CHECK_NONE = 0
    CHECK_INSTALLED = 1
    def __init__(self):
        self.upgrade = True
        self.downgrade = False
        self.exclusiveDeps = True
        self.sameProvideCoexits = False
        self.checkType = self.CHECK_NONE

class DependencyGraph:
    class CycleDependencyException(Exception):
        pass

    def __init__(self):
        self.preDict = {}

    def addPrerequisite(self, pkg, prerequisite):
        if pkg not in self.preDict:
            self.preDict[pkg] = set()
        self.preDict[pkg].add(prerequisite)
    
    def delPrerequisite(self, pkg, prerequisite = None):
        if pkg in self.preDict:
            if prerequisite is not None:
                self.preDict[pkg].remove(prerequisite)
            else:
                del self.preDict[pkg]

    def delPackage(self, pkg):
        if pkg in self.preDict:
            del self.preDict[pkg]
        for reqpkg in self.preDict:
            values = self.preDict[reqpkg]
            try:
                values.remove(pkg)
                if len(values) == 0:
                    del self.preDict[reqpkg]
            except KeyError, e:
                pass

    def updatePrerequisite(self, pkg, oldpre, newpre):
        if pkg not in self.preDict:
            return
        values = self.preDict[pkg]
        try:
            values.remove(oldpre)
            values.add(newpre)
        except KeyError, e:
            pass

    def iterate(self):
        outdegrees, depDict = dict(), dict()
        for package in self.preDict:
            prerequisites = self.preDict[package]
            if package not in outdegrees:
                outdegrees[package] = 0
            for prerequisite in prerequisites:
                if prerequisite is not None:
                    outdegrees[package] += 1
                    if prerequisite not in outdegrees:
                        outdegrees[prerequisite] = 0
                    depDict.setdefault(prerequisite, set()).add(package)

        stack = [x for x in outdegrees if outdegrees[x] == 0]
        count = 0
        while len(stack) > 0:
            package = stack.pop(0)
            count = count + 1
            yield package
            for dependent in depDict.get(package, []):
                outdegrees[dependent] -= 1
                if outdegrees[dependent] <= 0:
                    stack.append(dependent)
        if count != len(outdegrees):
            printDegreees = dict()
            for pkg in outdegrees:
                if outdegrees[pkg] != 0:
                    printDegreees[pkg] = outdegrees[pkg]
            Log.cout(Log.DEBUG, printDegreees)
            raise DependencyGraph.CycleDependencyException, "cycle dependent"

    def getTopologicalOrder(self):
        try:
            return [x for x in self.iterate()]
        except Exception, e:
            Log.cout(Log.ERROR, str(e))
            return None

    def copy(self):
        depGraph = DependencyGraph()
        depGraph.preDict.update(self.preDict)
        return depGraph

    def assign(self, other):
        self.preDict = {}
        self.preDict.update(other.preDict)

class ProvideComparer:
    def __init__(self, installRoot):
        self._installRoot = installRoot
        
    def _getInstallDir(self, pkg):
        if pkg.installed():
            return pkg.repo.id
        return self._installRoot

    def _provideDistance(self, reqDir, prvDir):
        if reqDir == prvDir:
            return 1
        if reqDir != '/' and prvDir == '/':
            return 0
        return -1

    def provideDistance(self, reqpkg, prvpkg):
        reqDir = self._getInstallDir(reqpkg)
        prvDir = self._getInstallDir(prvpkg)
        return self._provideDistance(reqDir, prvDir)

    def canProvide(self, reqpkg, prvpkg):
        return self.provideDistance(reqpkg, prvpkg) >= 0

    def compareProvide(self, reqpkg, pkg1, pkg2):
        if pkg1 is None:
            return -1
        if pkg2 is None:
            return 1
        
        dist1 = self.provideDistance(reqpkg, pkg1)
        dist2 = self.provideDistance(reqpkg, pkg2)
        if dist1 < 0 and dist2 < 0:
            return 0
        elif dist1 > dist2:
            return 1
        elif dist1 < dist2:
            return -1
        
        ret = arch.compareArchDistance(pkg1, pkg2, reqpkg.arch)
        if ret is None:
            return comparePoEVR(pkg1, pkg2)
        if ret is pkg1:
            return 1
        return -1

    def getBetterProvide(self, reqpkg, pkg1, pkg2):
        ret = self.compareProvide(reqpkg, pkg1, pkg2)
        if ret >= 0:
            return pkg1
        return pkg2

class ResolverContext:
    def __init__(self, ts, excludes, instContext):
        self.ts = ts
        self.excludes = excludes
        self.depGraph = None
        self.instContext = instContext
        self.checkedPkgs = set()
        self.pkgQueue = list()
        self.initOperation = INSTALL
        self.initPkgs = list()

    def copy(self):
        tmpts = self.ts.copy()
        tmpexcludes = self.excludes.copy()
        context = ResolverContext(tmpts, tmpexcludes, self.instContext)
        if self.depGraph is not None:
            context.depGraph = self.depGraph.copy()
        context.checkedPkgs = self.checkedPkgs
        context.initOperation = self.initOperation
        context.pkgQueue = self.pkgQueue
        context.initPkgs = self.initPkgs
        return context
        
class ResolverHelper:
    @staticmethod
    def checkProvideByRequire(provide, require):
        return ResolverHelper.checkProvideByRequires(provide, (require,))
    
    @staticmethod
    def checkProvideByRequires(provide, requires):
        if not requires:
            return True
        for require in requires:
            if not rpmutils.compareRange(require.getTuple(), provide.getTuple()):
                return False
        return True

    @staticmethod
    def checkPkgByRequires(pkg, requires):
        for require in requires:
            satisfied = False
            for provide in pkg.provides:
                if ResolverHelper.checkProvideByRequire(provide, require):
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True
    
    @staticmethod
    def checkPkgByRequire(pkg, require):
        return ResolverHelper.checkPkgByRequire(pkg, (require,))

    @staticmethod
    def getAndMergeRequires(pkg):
        requireDict = dict()
        for require in pkg.requires:
            if not ResolverHelper._omitRequire(require):
                requireDict.setdefault(require.name, []).append(require)
        return requireDict

    @staticmethod
    def _omitRequire(require):
        return require.name.startswith('/') or \
            require.name.startswith('rpmlib(')

    @staticmethod
    def filterPkgByRequires(pkgs, requireDict):
        """
        filter package in prvpkgs which does not match dependency like this:
        A >= 0.2.0 and A < 0.5.0
        """
        retpkgs = []
        for pkg in pkgs:
            if ResolverHelper._checkPkgSatisfying(pkg, requireDict):
                retpkgs.append(pkg)
        return retpkgs

    @staticmethod
    def _checkPkgSatisfying(pkg, requireDict):
        """
        return if pkg's provides match the dependency in requireDict 
        like: A >= 0.2.0 and A < 0.5.0
        """
        for provide in pkg.provides:
            if provide.flags is not None:
                requires = requireDict.get(provide.name)
                if not requires:
                    continue
                if not ResolverHelper.checkProvideByRequires(provide, requires):
                    return False
        return True

class RecursiveDepResolver:
    MAX_DEPTH = 20
    MAX_INSTALL_ERROR = 200
    def __init__(self, instContext, option = ResolverOption()):
        self.instContext = instContext
        self.installRoot = instContext.getInstallRoot()
        self.option = option
        self.installErrorCount = 0
        self.provideComparer = ProvideComparer(instContext.getInstallRoot())

    def install(self, packages):

        Log.cout(Log.INFO, 'Dependency resolve...')
        rsContext = self._initResolverContext(INSTALL, packages)
        pkgQueue = list()
        for package in packages:
            ret = self._install(package, rsContext, pkgQueue, depth = 0)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, 'Handle install package %s failed' % package)
                return ret, None, None
        ret = self._queue(pkgQueue, rsContext, depth = 0)
        if self.instContext.isRootInstall():
            return ret, rsContext.ts.getOperations(), None

        if ret != error.ERROR_NONE:
            return ret, None, None

        #for local install, check another time
        for pkg in rsContext.ts._operations.keys():
            if rsContext.ts.getOperation(pkg) == REMOVE:
                rsContext.ts.delOperation(pkg)
        rsContext.excludes.clear()
        rsContext.depGraph = DependencyGraph()
        rsContext.initOperation = CHECK

        for package in packages:
            ret = self._checkInstall(package, rsContext, pkgQueue, depth = 0)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, 'Check install package %s failed' % package)
                return ret, None, None
        topOrder = rsContext.depGraph.getTopologicalOrder()
        for package in packages:
            if package not in topOrder:
                topOrder.append(package)
        return ret, rsContext.ts.getOperations(), topOrder

    def remove(self, packages):
        Log.cout(Log.INFO, 'Dependency resolve...')
        rsContext = self._initResolverContext(REMOVE, [])
        rsContext.depGraph = DependencyGraph()
        pkgQueue = list()
        for package in packages:
            ret = self._remove(package, rsContext, pkgQueue, depth = 0)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, 'Handle remove package %s failed' % package)
                return ret, None, None
        ret = self._queue(pkgQueue, rsContext, depth = 0)
        topOrder = rsContext.depGraph.getTopologicalOrder()
        for package in packages:
            if package not in topOrder:
                topOrder.append(package)
        return ret, rsContext.ts.getOperations(), topOrder

    def check(self, packages):
        rsContext = self._initResolverContext(CHECK, packages)
        for package in packages:
            ret = self._check(package, rsContext, None, depth)
            if ret != error.ERROR_NONE:
                return ret
        return error.ERROR_NONE

    def _initResolverContext(self, initOp, packages):
        ts = Transaction(self.instContext)
        excludes = _Excludes()
        resolverContext = ResolverContext(ts, excludes, self.instContext)
        resolverContext.initOperation = initOp
        resolverContext.initPkgs = packages
        return resolverContext

    def _install(self, pkg, context, pkgQueue, depth):
        Log.cout(Log.DEBUG, self._outputTrace(depth, "install(%s)" % pkg))
        if depth > self.MAX_DEPTH:
            err = self._outputTrace(depth, "depth larger than %d" % self.MAX_DEPTH)
            Log.cout(Log.ERROR, err)
            return error.ERROR_INSTALL

        if self.installErrorCount > self.MAX_INSTALL_ERROR:
            err = self._outputTrace(depth, "install error count larger than %d" % self.MAX_INSTALL_ERROR)
            Log.cout(Log.ERROR, err)
            return error.ERROR_INSTALL

        if context.ts.installed(pkg) and \
                self.option.checkType == ResolverOption.CHECK_NONE:
            context.excludes.exclude(pkg)
            return error.ERROR_NONE

        if not context.ts.installed(pkg):
            context.ts.setOperation(pkg, INSTALL)
        context.excludes.exclude(pkg)

        recursive = False
        if pkgQueue is None:
            pkgQueue, recursive = list(), True
        ret = self._checkConflictAndProvide(pkg, context, pkgQueue, depth)
        if ret != error.ERROR_NONE:
            self.installErrorCount = self.installErrorCount + 1
            content = self._outputTrace(depth, 'Install pkg %s failed (%d times)'
                                        % (pkg, self.installErrorCount))
            Log.cout(Log.ERROR, content)
            return ret

        ret = self._check(pkg, context, pkgQueue, depth)
        if ret != error.ERROR_NONE:
            return ret
        
        if recursive and len(pkgQueue) > 0:
            ret = self._queue(pkgQueue, context, depth)
        return ret

    def _checkInstall(self, pkg, context, pkgQueue, depth):
        Log.cout(Log.DEBUG, self._outputTrace(depth, "checkInstall(%s)" % pkg))
        if depth > self.MAX_DEPTH:
            return error.ERROR_INSTALL
        context.ts.setOperation(pkg, INSTALL)
        context.excludes.exclude(pkg)

        if not pkg.installed():
            ret = self._checkConflictAndProvide(pkg, context, pkgQueue, depth)
            if ret != error.ERROR_NONE:
                return ret

        requireDict = ResolverHelper.getAndMergeRequires(pkg)
        for name, requires in requireDict.items():
            prvpkgs = self._getByProvides(requires, context)
            prvpkg = self._getBestInstalledProvide(pkg, prvpkgs, context)
            if not prvpkg:
                return error.ERROR_NONE
            if prvpkg is pkg:
                continue
            if context.excludes.excluded(prvpkg):
                self._addDependency(pkg, prvpkg, context, 'install')
                continue
            if self.getInstallDir(prvpkg) == self.installRoot:
                ret = self._checkInstall(prvpkg, context, pkgQueue, depth + 1)
                if ret != error.ERROR_NONE:
                    Log.cout(Log.ERROR, 'Check install package %s failed' % prvpkg)
                    return ret
                self._addDependency(pkg, prvpkg, context, 'install')
        return error.ERROR_NONE

    def _checkConflictAndProvide(self, pkg, context, pkgQueue, depth):
        ret = self._handleConflict(pkg, context, pkgQueue, depth)
        if ret != error.ERROR_NONE:
            content = self._outputTrace(depth, 'Handle conflict of pkg %s failed' % pkg)
            Log.cout(Log.ERROR, content)
            return ret
        ret = self._handleSameProvidePkg(pkg, context, pkgQueue, depth)
        if ret != error.ERROR_NONE:
            content = self._outputTrace(depth, 'Handle same provide of pkg %s failed' % pkg)
            Log.cout(Log.ERROR, content)
            return ret
        return error.ERROR_NONE
    
    def _handleConflict(self, pkg, context, pkgQueue, depth):
        """handle conflict in this pkg"""
        if pkg.conflicts:
            for conflict in pkg.conflicts:
                for conflictPkg in self._getByProvide(conflict, context):
                    ret = self._conflict(pkg, conflictPkg, context, pkgQueue, depth)
                    if ret != error.ERROR_NONE:
                        content = self._outputTrace(depth, 'Process conflict between %s and %s failed' % (pkg, conflictPkg))
                        Log.cout(Log.ERROR, content)
                        return ret

        #handle conflict with provides of pkg
        if pkg.provides:
            for provide in pkg.provides:
                for conflict in self._getByConflict(provide, context):
                    ret = self._conflict(pkg, conflict, context, pkgQueue, depth)
                    if ret != error.ERROR_NONE:
                        content = self._outputTrace(depth, 'Process conflict between %s and %s failed' % (conflict, pkg))
                        Log.cout(Log.ERROR, content)
                        return ret
        return error.ERROR_NONE

    def _conflict(self, pkg, conflict, context, pkgQueue, depth = 0):
        ts, excludes = context.ts, context.excludes
        if not ts.installed(conflict):
            excludes.exclude(conflict)
            return error.ERROR_NONE
        if excludes.excluded(conflict):
            logInfo = self._outputTrace(depth, 'failed: %s conflicts with %s' %\
                                            (pkg, conflict))
            Log.cout(Log.ERROR, logInfo)
            return error.ERROR_CONFLICT
        logInfo = self._outputTrace(depth, '%s conflicts with %s, remove %s' %\
                                        (pkg, conflict, conflict))
        Log.cout(Log.DEBUG, logInfo)
        ret = self._remove(conflict, context, pkgQueue, depth + 1)
        if ret == error.ERROR_NONE:
            self._addDependency(pkg, conflict, context, 'remove')
        return ret
    
    def _handleSameProvidePkg(self, pkg, context, pkgQueue, depth):
        while True:
            ret, notSatisfiedPkgs =\
                self._doHandleSameProvidePkg(pkg, context, pkgQueue, depth)
            if ret == error.ERROR_NONE:
                return ret
            if not notSatisfiedPkgs:
                return ret
            for package in notSatisfiedPkgs:
                ret = self._remove(package, context, pkgQueue, depth + 1)
                if ret != error.ERROR_NONE:
                    return ret
                self._addDependency(pkg, package, context, 'remove')

    def _doHandleSameProvidePkg(self, pkg, context, pkgQueue, depth):
        """
        If installed package with same name and can not coexist,
        we need to remove old package.
        """
        ts, excludes = context.ts, context.excludes
        for provide in pkg.provides:
            providers = self._getByProvide(Provide(name=provide.name), context)
            installedPkgs = []
            for package in providers:
                if package is pkg:
                    continue
                if not ts.installed(package):
                    excludes.exclude(package)
                else:
                    installedPkgs.append(package)
                
            for package in installedPkgs:
                coexists, notSatisfiedPkgs = self.coexists(pkg, provide, package, context)
                if coexists:
                    continue
                if not self._checkSamePkgWithOption(pkg, package, context, depth):
                    return error.ERROR_INSTALL, None
                ret = self._remove(package, context, pkgQueue, depth + 1)
                if ret != error.ERROR_NONE:
                    logInfo = self._outputTrace(depth, 'Handle same provide between %s and %s failed' % (pkg, package))
                    Log.cout(Log.ERROR, logInfo)
                    return ret, notSatisfiedPkgs
                self._addDependency(pkg, package, context, 'remove')
        return error.ERROR_NONE, None

    def coexists(self, pkg, provide, instPkg, context):
        if arch.canCoinstall(pkg.arch, instPkg.arch) or \
                self.option.sameProvideCoexits:
            return True, None
        instedPkgDir = self.getInstallDir(instPkg)
        toInstDir = self.getInstallDir(pkg)
        if toInstDir != '/':
            return self._localCoexists(pkg, provide, instPkg, context)
        for instProvide in instPkg.provides:
            if instProvide.name == provide.name:
                if toInstDir == instedPkgDir:
                    return False, None
        return True, None

    def _localCoexists(self, pkg, provide, instPkg, context):
        instPkgDir =  self.getInstallDir(instPkg)
        toInstDir = self.getInstallDir(pkg)
        instProvides = instPkg.provides
        instProvides = [x for x in instProvides if x.name == provide.name]
        if not instProvides:
            return True, None
        if instPkgDir == toInstDir:
            return False, None
        if instPkgDir != '/':
             return True, None

        notSatisfiedPkgs = []
        for instProvide in instProvides:
            req2PkgAndPrvs = self._getPkgAndProvideByRequire(instProvide, context)
            for requires, (reqpkgs, prvpkgs) in req2PkgAndPrvs.items():
                reqpkgs = [x for x in reqpkgs if toInstDir == 
                           self.getInstallDir(x) and context.ts.installed(x)]
                if not reqpkgs:
                    continue
                if pkg not in prvpkgs:
                    notSatisfiedPkgs.extend(reqpkgs)
        if notSatisfiedPkgs:
            return False, notSatisfiedPkgs
        return True, None

    def getInstallDir(self, pkg):
        if pkg.installed():
            return pkg.repo.id
        return self.installRoot

    def _checkSamePkgWithOption(self, pkg, installedPkg, context, depth):
        if pkg.name != installedPkg.name:
            return True
        if pkg in context.initPkgs or not installedPkg.installed():
            return True
        if not self.option.downgrade and comparePoEVR(pkg, installedPkg) < 0:
            content = self._outputTrace(depth, 'Failed: try to downgrade pkg %s'\
                                            % installedPkg)
            Log.cout(Log.ERROR, content)
            return False
        if not self.option.upgrade and comparePoEVR(pkg, installedPkg) > 0:
            content = self._outputTrace(depth, 'Failed: try to upgrade pkg %s'\
                                            % installedPkg)
            Log.cout(Log.ERROR, content)
            return False
        return True

    def _check(self, pkg, context, pkgQueue, depth):
        Log.cout(Log.DEBUG, self._outputTrace(depth, 'check(%s)' % pkg))
        ts, excludes = context.ts, context.excludes
        ret = error.ERROR_NONE
        context.checkedPkgs.add(pkg)

        requireDict = ResolverHelper.getAndMergeRequires(pkg)
        #May be need sort this require.
        items = self._sortRequireByName(requireDict)
        for name, requires in items:
            prvpkgs = self._getByProvides(requires, context)
            if pkg in prvpkgs:
                continue
            prvpkgs = ResolverHelper.filterPkgByRequires(prvpkgs, requireDict)
            prvpkg = self._getBestInstalledProvide(pkg, prvpkgs, context)
            if prvpkg is not None:
                ret = self._doCheck(prvpkg, context, pkgQueue, depth)
                if ret != error.ERROR_NONE:
                    return ret
                if self._needUpgradeLocalProvide(pkg, name, prvpkg, context):
                    self._upgradeLocalProvide(pkg, requires, prvpkgs, context, pkgQueue)
                continue
            if context.initOperation == CHECK:
                return error.ERROR_CHECK
            prvpkgs = self._filterAndSortPackages(prvpkgs, pkg)
            pkgQueue.append((INSTALL, pkg, requires, prvpkgs))
        return error.ERROR_NONE

    def _needUpgradeLocalProvide(self, pkg, requireName, prvpkg, context):
        if self.installRoot == '/' or self.getInstallDir(prvpkg) != '/':
            return False

        providers = self._getByProvide(Provide(requireName), context)
        for package in providers:
            if context.ts.installed(package) and\
                    self.getInstallDir(package) == self.installRoot:
                return True
        return False

    def _upgradeLocalProvide(self, pkg, requires, prvpkgs, context, pkgQueue):
        newPrvPkgs = [package for package in prvpkgs\
                          if not context.ts.installed(package)]
        newPrvpkgs = self._filterAndSortPackages(newPrvPkgs, pkg)
        pkgQueue.append((INSTALL, pkg, requires, newPrvpkgs))            
        return error.ERROR_NONE

    def _doCheck(self, pkg, context, pkgQueue, depth):
        if not self._needCheck(pkg, context):
            return error.ERROR_NONE
        context.excludes.exclude(pkg)
        ret = self._check(pkg, context, pkgQueue, depth + 1)
        context.excludes.unexclude(pkg)
        return ret

    def _needCheck(self, pkg, context):
        if context.excludes.excluded(pkg) or \
                self.getInstallDir(pkg) != self.installRoot:
            return False

        if pkg in context.checkedPkgs:
            return False

        if context.initOperation == CHECK:
            return True
        if self.option.checkType == ResolverOption.CHECK_INSTALLED and \
                pkg.installed():
            return True
        return False

    def _remove(self, pkg, context, pkgQueue, depth):
        Log.cout(Log.DEBUG, self._outputTrace(depth, 'remove(%s)' % pkg))
        ts, excludes = context.ts, context.excludes
        if not ts.installed(pkg):
            return error.ERROR_NONE

        if depth > self.MAX_DEPTH or not self._canRemove(pkg, context):
            Log.cout(Log.ERROR, self._outputTrace(depth, 'can not remove %s' % pkg))
            return error.ERROR_REMOVE
        
        recursive = False
        if pkgQueue is None:
            pkgQueue, recursive = list(), True
        ts.setOperation(pkg, REMOVE)
        excludes.exclude(pkg)
        
        for provide in pkg.provides:
            ret = self._removeProvide(pkg, provide, context, pkgQueue, depth)
            if ret != error.ERROR_NONE: 
                Log.cout(Log.ERROR, self._outputTrace(depth, "remove %s failed" % pkg))
                return ret
        Log.cout(Log.DEBUG, self._outputTrace(depth, "remove all provide: %s" % pkg))

        ret = error.ERROR_NONE
        #if recursive and len(pkgQueue) > 0:
        #    ret = self._queue(pkgQueue, context, depth)
        if ret != error.ERROR_NONE:
            Log.cout(Log.DEBUG, self._outputTrace(depth, "remove %s failed" % pkg))
        else:
            Log.cout(Log.DEBUG, self._outputTrace(depth, "remove %s success" % pkg))
        return ret

    def _canRemove(self, pkg, context):
        installRoot = self.instContext.getInstallRoot()
        pkgInstallRoot = self.getInstallDir(pkg)
        return installRoot == pkgInstallRoot


#        if installRoot == '/':
#            if pkgInstallRoot != '/':
#                return False
#        else:
#            if pkgInstallRoot == '/' or pkgInstallRoot != installRoot:
#                return False
#        return True

    def _removeProvide(self, pkg, provide, context, pkgQueue, depth):
        ts, excludes = context.ts, context.excludes
        req2PkgAndProvide = self._getPkgAndProvideByRequire(provide, context)
        for require, (reqpkgs, prvpkgs) in req2PkgAndProvide.items():
            reqpkgs = [x for x in reqpkgs if ts.installed(x)]
            reqpkgs = [x for x in reqpkgs if not 
                       self._getInstalledProvide(x, prvpkgs, context)]
            if not reqpkgs:
                continue

            prvpkgs = [x for x in prvpkgs if not excludes.excluded(x)]
            prvpkgs = self._filterAndSortPackages(prvpkgs, pkg)
            candRet = error.ERROR_NONE
            if prvpkgs:
                candRet, instpkg = \
                    self._installCandidates(pkg, prvpkgs, context, 
                                            pkgQueue, depth)
                if candRet == error.ERROR_NONE:
                    for reqpkg in reqpkgs:
                        self._updateDependency(reqpkg, pkg, instpkg, context)
            if not prvpkgs or candRet != error.ERROR_NONE:
                ret = self._removePackages(reqpkgs, context, pkgQueue, depth)
                if ret != error.ERROR_NONE:
                    return ret
                for reqpkg in reqpkgs:
                    self._addDependency(pkg, reqpkg, context, 'remove')
        return error.ERROR_NONE

    def _getLocalProvide(self, pkg, require):
        sack = pkg.repo.getPackageSack()
        if sack is None:
            return {}
        return sack.getProvides(require)

    def _installCandidates(self, pkg, prvpkgs, context, pkgQueue, depth):
        retValue = error.ERROR_INSTALL
        for prvpkg in prvpkgs:
            tmpContext = context.copy()
            ret = self._install(prvpkg, tmpContext, None, depth + 1)
            if ret != error.ERROR_NONE:
                if ret == error.ERROR_EXCLUSIVE_DEPS:
                    retValue = error.ERROR_EXCLUSIVE_DEPS
                Log.cout(Log.DEBUG, self._outputTrace(depth + 1, 'install %s failed' % prvpkg))
                continue
            self._outputTrace(depth + 1, 'install %s success' % prvpkg)
            context.ts.assign(tmpContext.ts)
            return ret, prvpkg
        return retValue, None

    def _removePackages(self, pkgs, context, pkgQueue,  depth):
        for pkg in pkgs:
            if context.excludes.excluded(pkg):
                Log.cout(Log.ERROR, self._outputTrace(depth, 'remove excluded: %s' % pkg))
                return error.ERROR_REMOVE

            if self._exclusiveDeps(pkg, context):
                Log.cout(Log.ERROR, self._outputTrace(depth, 'exclusive deps: %s' % pkg))
                return error.ERROR_EXCLUSIVE_DEPS

            ret = self._remove(pkg, context, pkgQueue, depth + 1)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, self._outputTrace(depth, 'remove %s failed' % pkg))
                return ret
        return error.ERROR_NONE

    def _exclusiveDeps(self, pkg, context):
        return self.option.exclusiveDeps and context.initOperation == INSTALL \
            and pkg.installed() and context.ts.getOperation(pkg) != REMOVE

    def _queue(self, pkgQueue, context, depth):
        if len(pkgQueue) == 0:
            return error.ERROR_NONE
        Log.cout(Log.DEBUG, self._outputTrace(depth, "queue"))

        ret = error.ERROR_NONE
        while True:
            tmpQueue, hasSuccess = list(), False
            while len(pkgQueue) > 0:
                item = pkgQueue.pop(0)
                if item[0] == INSTALL:
                    ret = self._handleInstallItem(pkgQueue, item, context, depth)
                elif item[0] == REMOVE:
                    ret = self._handleRemoveItem(pkgQueue,item, context, depth)
                if ret == error.ERROR_NONE:
                    hasSuccess = True
                elif ret == error.ERROR_EXCLUSIVE_DEPS:
                    tmpQueue.append(item)
                else:
                    opt = 'Handle'
                    if item[0] == INSTALL:
                        opt = 'Install'
                    elif item[0] == REMOVE:
                        opt = 'Remove'
                    content = self._outputTrace(depth, '%s pkg %s failed' % (opt, item[1]))
                    Log.cout(Log.ERROR, content)
                    return ret
            if len(tmpQueue) == 0:
                return error.ERROR_NONE
            if not hasSuccess:
                return error.ERROR_EXCLUSIVE_DEPS
            pkgQueue.extend(tmpQueue)
        return ret

    def _handleInstallItem(self, pkgQueue, item, context, depth):
        optype, pkg, requires, prvpkgs = item
        #self._outputTrace(depth, 'handle_install(%s)' % str(prvpkgs))

        bestProvidePkg = self._getBestInstalledProvide(pkg, prvpkgs, context)
        if bestProvidePkg:
            return error.ERROR_NONE 

        prvpkgs = [x for x in prvpkgs if not context.excludes.excluded(x)]
        if not prvpkgs:
            Log.cout(Log.ERROR, self._outputTrace(depth, "install %s failed: no provide %s" % (pkg, requires)))
            return error.ERROR_NO_PROVIDES

        candRet, instpkg = \
            self._installCandidates(pkg, prvpkgs, context, pkgQueue, depth)
        return candRet

    def _handleRemoveItem(self, pkgQueue, item, context, depth):
        kind, pkg, provide, reqpkgs, prvpkgs = item
        ts, excludes = context.ts, context.excludes
        reqpkgs = [x for x in reqpkgs if ts.installed(x)]
        reqpkgs = [x for x in reqpkgs if not 
                   self._getInstalledProvide(x, prvpkgs, context)]
        if not reqpkgs:
            return error.ERROR_NONE

        prvpkgs = [x for x in prvpkgs if not excludes.excluded(x)]
        prvpkgs = self._filterAndSortPackages(prvpkgs,  pkg)
        candRet = error.ERROR_NONE
        if prvpkgs:
            candRet, instpkg = \
                self._installCandidates(pkg, prvpkgs, context, pkgQueue, depth)
            if candRet == error.ERROR_NONE:
                for reqpkg in reqpkgs:
                    self._updateDependency(reqpkg, pkg, instpkg, context)
        if not prvpkgs or candRet != error.ERROR_NONE:
            ret = self._removePackages(reqpkgs, context, pkgQueue, depth)
            if ret != error.ERROR_NONE:
                return ret
        return error.ERROR_NONE

    def _getBestInstalledProvide(self, reqpkg, prvpkgs, context):
        prvpkgs = self._getInstalledProvide(reqpkg, prvpkgs, context)
        retpkg = None
        for prvpkg in prvpkgs:
            retpkg = self.provideComparer.getBetterProvide(reqpkg, retpkg, prvpkg)
        return retpkg

    def _getInstalledProvide(self, reqpkg, prvpkgs, context):
        retpkgs = []
        for prvpkg in prvpkgs:
            if context.ts.installed(prvpkg) and \
                    self.provideComparer.canProvide(reqpkg, prvpkg):
                retpkgs.append(prvpkg)
        return retpkgs

    def _updateDependency(self, pkg, oldprvpkg, prvpkg, context):
        if context.depGraph:
            Log.cout(Log.INFO, 'update depend: %s => %s => %s' % (pkg, oldprvpkg, prvpkg))
            context.depGraph.updatePrerequisite(pkg, oldprvpkg, prvpkg)

    def _addDependency(self, pkg, prvpkg, context, relation):
        if context.depGraph:
            Log.cout(Log.INFO, 'add %s depend: %s => %s' % (relation, pkg, prvpkg))
            context.depGraph.addPrerequisite(pkg, prvpkg)

    def _delDependency(self, pkg, prvpkg, context):
        if context.depGraph:
            Log.cout(Log.INFO, 'del depend: %s => %s' % (pkg, prvpkg))
            context.depGraph.delPrerequisite(pkg, prvpkg)

    def _getByRequire(self, provide, context):
        """
        return {pkg: requires} that pkg requires the provide
        which must satisfy the requires of this pkg
        """
        ts = context.ts
        pkg2Requires = ts.getByRequire(Require(name = provide.name))
        for pobj, requires in pkg2Requires.items():
            if not ResolverHelper.checkProvideByRequires(provide, requires):
                del pkg2Requires[pobj]
        return pkg2Requires

    def _getByProvide(self, require, context):
        return context.ts.getByProvide(require)

    def _getByConflict(self, conflict, context):
        return context.ts.getByConflict(conflict)

    def _getByProvides(self, requires, context):
        """
        return  retpkgs contains package match the requires
        """
        pkgPrvDict = dict()
        for require in requires:
            for prvpkg in context.ts.getByProvide(require):
                pkgPrvDict.setdefault(prvpkg, []).append(require)

        retpkgs = []
        for prvpkg in pkgPrvDict:
            if len(pkgPrvDict[prvpkg]) == len(requires):
                retpkgs.append(prvpkg)
        return retpkgs

    def _getPkgAndProvideByRequire(self, provide, context):
        """
        Return {require, [require-packages], [provide-packages]},
        """
        req2PkgAndProvide = {}
        for pkg, requires in self._getByRequire(provide, context).items():
            for req in requires:
                req2Pkgs = req2PkgAndProvide.setdefault(req, [set(), set()])[0]
                req2Pkgs.add(pkg)
        
        for req in req2PkgAndProvide:
            reqPkgs, reqProvides = req2PkgAndProvide.get(req)
            pkg2Provides = self._getByProvide(req, context)
            reqProvides.update(pkg2Provides.keys())
        return req2PkgAndProvide

    def _filterAndSortPackages(self, pkgs, oldpkg = None):
        if oldpkg is None:
            compareArch = arch.getBestArch()
        else:
            compareArch = oldpkg.arch

        pkgSorter = PackageArchSorter(compareArch)
        pkgs = pkgSorter.sort(pkgs)

        archFilter = PackageArchFilter(arch.getBestArch())
        pkgs = archFilter.filter(pkgs)
        if len(pkgs) < 2:
            return pkgs
        
        #distinct same version pkg
        result = [pkgs[0]]
        for index in range(1, len(pkgs)):
            if result[-1].getTuple() != pkgs[index].getTuple():
                result.append(pkgs[index])
        return result

    def _outputTrace(self, depth, msg):
        indent = ''
        for index in range(depth):
            indent = indent + '  '
        return '%s[%03d] %s' % (indent, depth, msg)

    def _sortRequireByName(self, requireDict):
        return sorted(requireDict.items(), key=lambda item:item[0])

if __name__ == '__main__':
    pass

    
