#! /usr/bin/python

import rpmutils
from package_object import *
from rpm_header_package import *

class PackageUtil:
    @staticmethod
    def comparePkg(pkg1, pkg2):
        if pkg1 and not pkg2:
            return 1
        elif not pkg1 and pkg2:
            return -1
        elif not pkg1 and not pkg2:
            return 0
        ret = cmp(pkg1.name, pkg2.name)
        if ret == 0:
            (e1, v1, r1) = (pkg1.epoch, pkg1.version, pkg1.release)
            (e2, v2, r2) = (pkg2.epoch, pkg2.version, pkg2.release)
            return rpmutils.compareEVR((e1, v1, r1), (e2, v2, r2))
        return ret

    @staticmethod
    def checkRequire(pkg, checkObj):
        return PackageUtil._check('require', pkg, checkObj)

    @staticmethod
    def checkProvide(pkg, checkObj):
        return PackageUtil._check('provide', pkg, checkObj)

    @staticmethod
    def checkConflict(pkg, checkObj):
        return PackageUtil._check('conflict', pkg, checkObj)

    @staticmethod
    def checkObsolete(pkg, checkObj):
        return PackageUtil._check('obsolete', pkg, checkObj)

    @staticmethod
    def matchingRequire(pkg, matchObj):
        return PackageUtil._match('require', pkg, matchObj)

    @staticmethod
    def matchingProvide(pkg, matchObj):
        return PackageUtil._match('provide', pkg, matchObj)

    @staticmethod
    def matchingConflict(pkg, matchObj):
        return PackageUtil._match('conflict', pkg, matchObj)

    @staticmethod
    def matchingObsolete(pkg, matchObj):
        return PackageUtil._match('obsolete', pkg, matchObj)

    @staticmethod
    def _check(checkType, pkg, checkObj):
        checkContent = PackageUtil._getContentByType(pkg, checkType)
        if checkContent is None:
            return False
        if checkObj in checkContent:
            return True
        if checkObj.flags is None:
            for obj in checkContent:
                if obj.name == checkObj.name:
                    return True
        else:
            return bool(PackageUtil._match(checkType, pkg, checkObj))
        return False

    @staticmethod
    def _match(matchType, pkg, matchObj):
        result = []
        matchContent = PackageUtil._getContentByType(pkg, matchType)
        if matchContent is None:
            return False
        for obj in matchContent:
            (name, flags, (epoch, version, release)) = obj.getTuple()
            if name != matchObj.name:
                continue
            if flags == '=':
                flags = 'EQ'
            if flags != 'EQ' and matchType == 'provide':
                if epoch is None:
                    epoch = pkg.epoch
                if version is None:
                    version = pkg.version
                if release is None:
                    release = pkg.release
            if rpmutils.compareRange(matchObj.getTuple(), 
                                     (name, flags, (epoch, version, release))):
                result.append(obj)
        return result

    @staticmethod    
    def _getContentByType(pkg, checkType):
        checkContent = None
        if checkType == 'require':
            checkContent = pkg.requires
        elif checkType == 'provide':
            checkContent = pkg.provides
        elif checkType == 'conflict':
            checkContent = pkg.conflicts
        elif checkType == 'obsolete':
            checkContent = pkg.obsoletes
        return checkContent

    @staticmethod    
    def getPkgNameVersion(pkg):
        if not pkg or not pkg.name or not pkg.version:
            return None
        pkgDirName = '%s-%s' % (pkg.name, pkg.version)
        if pkg.release:
            pkgDirName = '%s-%s' % (pkgDirName, pkg.release)
        if pkg.arch:
            pkgDirName = '%s.%s' % (pkgDirName, pkg.arch)            
        if pkg.epoch and pkg.epoch != '0':
            pkgDirName = '%s:%s' % (pkg.epoch, pkgDirName)
        return pkgDirName


if __name__ == "__main__":
    import cache
    pkg1 = cache.Package("A", "0.2.0")
    pkg2 = PackageObject("A", "0.1.0", "rc2")
    print PackageUtil.comparePkg(pkg1, pkg2)
    
    requires = []
    requires.append(cache.Meta("B", "GT", "0", "6.0.0"))
    requires.append(cache.Meta("B", "LT", "0", "2.0.0"))
    pkg1.requires = requires
    matchObj = Require("B", "EQ", "0", "7.0.0")
    print PackageUtil.matchingRequire(pkg1, matchObj)
