#! /usr/bin/python

from  package_util import PackageUtil

class PackageSackBase:
    def __init__(self):
        pass
    
    def addPackageObject(self, obj):
        """add a pkgobject to the packageSack"""
        raise NotImplementedError()

    def deletePackageObject(self, obj):
        """delete a pkgobject"""
        raise NotImplementedError()

    def returnPackages(self):
        """return list of all packages"""
        raise NotImplementedError()
    
    def populate(self, metaType):
        """populate info of packagesack, such as filelists"""
        pass

    def getRequires(self, require):
        raise NotImplementedError()

    def getProvides(self, provide):
        raise NotImplementedError()

    def searchPkg(self, name=None, epoch=None, version=None,
                  release=None, arch=None):
        raise NotImplementedError()

    def searchPkgByName(self, name):
        raise NotImplementedError()

    def searchPkgByRequire(self, name):
        raise NotImplementedError()

    def searchPkgByConflict(self, name):
        raise NotImplementedError()

    def searchPkgByObsolete(self, name):
        raise NotImplementedError()

    def searchPkgByProvide(self, name):
        raise NotImplementedError()

    def searchPkgByFile(self, name):
        return NotImplementedError()

class PackageSack(PackageSackBase):
    def __init__(self):
        self.repoPkgList = []
        self.requirePkgDict = {}
        self.providePkgDict = {}
        self.conflictPkgDict = {}
        self.obsoletePkgDict = {}
        self.tuplePkgDict = {}
        self.filePkgDict = {}
        self.namePkgDict = {}
        self.indexBuilt = False

    def addPackageObject(self, pkg):
        self.repoPkgList.append(pkg)
        if self.indexBuilt:
            self._addToIndex(pkgObject)

    def deletePackageObject(self, pkg):
        try:
            self.repoPkgList.remove(pkg)
        except Exception:
            pass
        if self.indexBuilt:
            self._delFromIndex(pkg)

    def buildIndex(self):
        self.clearIndex()
        for pkgObject in self.repoPkgList:
            self._addToIndex(pkgObject)
        self.indexBuilt = True

    def clearIndex(self):
         self.requirePkgDict = {}
         self.providePkgDict = {}
         self.conflictPkgDict = {}
         self.obsoletePkgDict = {}
         self.filePkgDict = {}
         self.tuplePkgDict = {}
         self.namePkgDict = {}
         self.indexBuilt = False

    def _addToIndex(self, pkgObject):
        if pkgObject.getTuple() in self.tuplePkgDict:
            # same package exist multi times, skip
            return 
        if pkgObject.requires:
            for require in pkgObject.requires:
                self.requirePkgDict.setdefault(require.name, []).append(pkgObject)
        if pkgObject.provides:
            for provide in pkgObject.provides:
                self.providePkgDict.setdefault(provide.name, []).append(pkgObject)
        if pkgObject.conflicts:
            for conflict in pkgObject.conflicts:
                self.conflictPkgDict.setdefault(conflict.name, []).append(pkgObject)
        if pkgObject.obsoletes:
            for obsolete in pkgObject.obsoletes:
                self.obsoletePkgDict.setdefault(obsolete.name, []).append(pkgObject)
        self.namePkgDict.setdefault(pkgObject.name, []).append(pkgObject)
        self.tuplePkgDict.setdefault(pkgObject.getTuple(), []).append(pkgObject)

    def _delFromIndex(self, pkg):
        if pkg.requires:
            for require in pkg.requires:
                self._delFromDict(self.requirePkgDict, require.name, pkg)
        if pkg.provides:
            for provide in pkg.provides:
                self._delFromDict(self.providePkgDict, provide.name, pkg)
        if pkg.conflicts:
            for conflict in pkg.conflicts:
                self._delFromDict(self.conflictPkgDict, conflict.name, pkg)
        if pkg.obsoletes:
            for obsolete in pkg.obsoletes:
                self._delFromDict(self.obsoletePkgDict, obsolete.name, pkg)
        self._delFromDict(self.namePkgDict, pkg.name, pkg)
        self._delFromDict(self.tuplePkgDict, pkg.getTuple(), pkg)

    def _delFromDict(self, dictElem, key, value):
        if not dictElem.has_key(key):
            return
        try:
            dictElem[key].remove(value)
        except Exception:
            pass
        if len(dictElem[key]) == 0:
            del dictElem[key]

    def getPkgs(self):
        return self.repoPkgList

    def getRequires(self, obj):
         '''return dict: {packageObject:[require, require, ...]}'''
         if not self.indexBuilt:
             self.buildIndex()
         result = {}
         for pkgObject in self.requirePkgDict.get(obj.name, []):
             requires = PackageUtil.matchingRequire(pkgObject, obj)
             if requires:
                 result[pkgObject] = requires
         return result

    def getProvides(self, obj):
         '''return dict: {packageObject:[provide, provide, ...]}'''
         if not self.indexBuilt:
             self.buildIndex()
         result = {}
         for pkgObject in self.providePkgDict.get(obj.name, []):
             provides = PackageUtil.matchingProvide(pkgObject, obj)
             if provides:
                 result[pkgObject] = provides
         #if obj.name[0] == '/':
         #    tmpProvide = Require()
         #    tmpProvide.name = name
         #    for pkgObject in self.searchFilesByName(name):
         #        result.setdefault(pkgObject, []).append(tmpProvide)
         return result

    def getConflicts(self, obj):
        if not self.indexBuilt:
            self.buildIndex()
        result = {}
        for pkgObject in self.conflictPkgDict.get(obj.name, []):
            conflicts = PackageUtil.matchingConflict(pkgObject, obj)
            if conflicts:
                result[pkgObject] = conflicts
        return result

    def searchPkg(self, name=None, epoch=None, version=None,
                  release=None, arch=None):
        if not self.indexBuilt:
            self.buildIndex()
        tupleKey = (name, epoch, version, release, arch)
        if self.tuplePkgDict.has_key(tupleKey):
            return self.tuplePkgDict[tupleKey]
        result = []
        if name is not None:
            pkgs = self.searchPkgByName(name)
            for pkg in pkgs:
                if (epoch and pkg.epoch != epoch) or\
                        (version and pkg.version != version) or\
                        (release and pkg.release != release) or\
                        (arch and pkg.arch != arch):
                    continue
                result.append(pkg)
        return result

    def searchPkgByName(self, name):
        if not self.indexBuilt:
            self.buildIndex()
        if self.namePkgDict.has_key(name):
            return self.namePkgDict[name]
        return []

    #maybe dup
    def searchPkgByRequire(self, name):
        if not self.indexBuilt:
            self.buildIndex()
        if self.requirePkgDict.has_key(name):
            return self.requirePkgDict[name]
        return []

    def searchPkgByProvide(self, name):
        if not self.indexBuilt:
            self.buildIndex()
        result = []
        #if name[0] == '/':
        #    result.append(self.searchFilesByName(name))
        if self.providePkgDict.has_key(name):
            result += self.providePkgDict[name]
        return result

    def searchPkgByConflict(self, name):
         if not self.indexBuilt:
             self.buildIndex()
         if self.conflictPkgDict.has_key(name):
             return self.conflictPkgDict[name]
         return []

    def searchPkgByObsolete(self, name):
         if not self.indexBuilt:
             self.buildIndex()
         if self.obsoletePkgDict.has_key(name):
             return self.obsoletePkgDict[name]
         return []

    def searchPkgByFile(self, name):
         if not self.indexBuilt:
             self.buildIndex()
         if self.filePkgDict.has_key(name):
             return self.filePkgDict[name]
         return []

class MultiPackageSack(PackageSack):
    def __init__(self):
        PackageSack.__init__(self)
        self.packageSacks = {}
    
    def addPackageSack(self, repoid, packageSack):
        self.packageSacks[repoid] = packageSack

    def getPackageSacks(self):
        return self.packageSacks.values()

    def addPackageObject(self, pkgObject):
        return

    def deletePackageObject(self, packageObject):
        for sack in self.packageSacks.values():
            sack.deletePackageObject(packageObject)

    def buildIndex(self):
        for sack in self.packageSacks.values():
            sack.buildIndex()

    def populate(self, metaType):
        for sack in self.packageSacks.values():
            sack.populate(metaType)

    def getRequires(self, require):
        '''return dict: {packageObject:[require, require, ...]}'''
        return self._aggregateDictResult('getRequires', require)

    def getProvides(self, provide):
        '''return dict: {packageObject:[provide, provide, ...]}'''
        return self._aggregateDictResult('getProvides', provide)

    def getConflicts(self, conflict):
        '''return dict: {packageObject:[provide, provide, ...]}'''
        return self._aggregateDictResult('getConflicts', conflict)

    def getPkgs(self):
        repo2Pkgs = {}
        for repoid, sack in self.packageSacks.items(): 
            repo2Pkgs[repoid] = sack.getPkgs()
        return repo2Pkgs

    def searchPkg2(self, name=None, epoch=None, version=None,
                   release=None, arch=None):
        repo2Pkgs = {}
        for repoid, sack in self.packageSacks.items(): 
            repo2Pkgs[repoid] = sack.searchPkg(name, epoch, version, release, arch)
        return repo2Pkgs

    def searchPkg(self, name=None, epoch=None, version=None,
                  release=None, arch=None):
        return self._aggregateListResult('searchPkg', name, epoch,
                                         version, release, arch)

    def searchPkgByName(self, name):
        return self._aggregateListResult('searchPkgByName', name)

    def searchPkgByRequire(self, name):
        return self._aggregateListResult('searchPkgByRequireName', name)

    def searchPkgByProvide(self, name):
        return self._aggregateListResult('searchPkgByProvideName', name)

    def searchPkgByConflict(self, name):
        return self._aggregateListResult('searchPkgByConflictName', name)

    def searchPkgByObsolete(self, name):
        return self._aggregateListResult('searchPkgByObsoleteName', name)

    def searchPkgByFile(self, name):
        return self._aggregateListResult('searchPkgByFileName', name)

    def _aggregateListResult(self, methodName, *args):
        result = []
        for sack in self.packageSacks.values():
            if hasattr(sack, methodName):
                method = getattr(sack, methodName)
                try:
                    sackResult = apply(method, args)
                except Exception,e:
                    continue
                if sackResult:
                    result.extend(sackResult)
        return result

    def _aggregateDictResult(self, methodName, *args):
        result = {}
        for sack in self.packageSacks.values():
            if hasattr(sack, methodName):
                method = getattr(sack, methodName)
                try:
                    sackResult = apply(method, args)
                except Exception:
                    continue
                if sackResult:
                    result.update(sackResult)
        return result

if __name__ == "__main__":
    from package_object import *
    import cache
    sack = PackageSack()

    pkg1 = RpmPackageBase(None, "A", "1.1.1", "rc1")
    pkg1.requires.append(Require("B", "GT", "0", "1.1.0"))
    pkg1.requires.append(Require("B", "LT", "0", "3.1.0"))
    pkg1.requires.append(Require("C", "GT", "0", "1.1.0"))
    pkg1.requires.append(Require("D", "LT", "0", "3.1.0"))
    pkg1.provides.append(Require("A", "EQ", "0", "1.1.1"))
    pkg1.provides.append(Require("liba"))
    sack.addPackageObject(pkg1)

    pkg2 = RpmPackageBase(None, "B", "1.2.1", "rc1")
    pkg2.requires.append(Require("C", "GT", "0", "1.1.0"))
    pkg2.requires.append(Require("C", "LT", "0", "3.1.0"))
    pkg2.requires.append(Require("D", "GT", "0", "1.1.0"))
    pkg2.requires.append(Require("E", "LT", "0", "3.1.0"))
    pkg2.provides.append(Require("B", "EQ", "0", "1.2.1"))
    pkg2.provides.append(Require("libb"))
    sack.addPackageObject(pkg2)

    pkg3 = RpmPackageBase(None, "B", "4.2.1", "rc1")
    pkg3.requires.append(Require("C", "GT", "0", "1.1.0"))
    pkg3.requires.append(Require("C", "LT", "0", "3.1.0"))
    pkg3.requires.append(Require("D", "GT", "0", "1.1.0"))
    pkg3.requires.append(Require("E", "LT", "0", "3.1.0"))
    pkg3.provides.append(Require("B", "EQ", "0", "4.2.1"))
    pkg3.provides.append(Require("libb"))
    sack.addPackageObject(pkg3)

    pkg4 = cache.Package("B", "1.4.1", "rc1")
    requires = []
    requires.append(cache.Meta("C", "GT", "0", "1.1.0"))
    requires.append(cache.Meta("D", "LT", "0", "3.1.0"))
    pkg4.requires = requires
    provides = []
    provides.append(cache.Meta("B", "EQ", "0", "1.4.1"))
    provides.append(cache.Meta("libb"))
    pkg4.provides = provides
    sack.addPackageObject(pkg4)

    sack.buildIndex()

    print "Test search by pkg"
    print sack.searchPkg(name="A", version="9.0")

    print "Test search by name"
    print sack.searchPkgByName("B")

    print "Test search by require"
    print sack.searchPkgByRequire("A")
    print sack.searchPkgByRequire("B")
    print sack.searchPkgByRequire("C")

    print "Test search by provide"
    print sack.searchPkgByProvide("A")
    print sack.searchPkgByProvide("B")
    print sack.searchPkgByProvide("C")
    print sack.searchPkgByProvide("liba")

    print "Test get requires"
    print sack.getRequires(cache.Meta("A"))
    print sack.getRequires(cache.Meta("B"))
    print sack.getRequires(cache.Meta("C"))
    print sack.getRequires(cache.Meta(name="D", flags="EQ", version="6.0"))
    print sack.getRequires(cache.Meta("E"))

    print "Test get provides"
    print sack.getProvides(cache.Meta("A"))
    print sack.getProvides(cache.Meta("B"))
    print sack.getProvides(cache.Meta(name="B", flags="LT", version="3.0.0"))
    print sack.getProvides(cache.Meta(name="B", flags="GT", version="3.0.0"))


    sack.clearIndex()
