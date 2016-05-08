#! /usr/bin/python

import rpm
import rpmutils
from package_object import *
from repository import FakeRepository

class RpmHeaderPackage(RpmPackageBase):
    def __init__(self, header, repo):
        RpmPackageBase.__init__(self, repo)
        self.header = header
        self.pkgid = None
        self.initFromHeader(header)

    def initFromHeader(self, header):
        self.name = self.header[rpm.RPMTAG_NAME]
        self.arch = self.header[rpm.RPMTAG_ARCH]
        if not self.arch:
            self.arch = 'noarch'
        self.epoch = self.header[rpm.RPMTAG_EPOCH]
        if self.epoch is None:
            self.epoch = '0'
        else:
            self.epoch = str(self.epoch)
        self.version = self.header[rpm.RPMTAG_VERSION]
        self.release = self.header[rpm.RPMTAG_RELEASE]
        self.summary = self.header[rpm.RPMTAG_SUMMARY] or ''
        self.description = self.header[rpm.RPMTAG_DESCRIPTION] or ''
        self.packagesize = self.header[rpm.RPMTAG_SIZE] 
        self.pkgid = self.header[rpm.RPMTAG_SHA1HEADER]
        self.prefixes = self.header[rpm.RPMTAG_PREFIXES]
        if not self.pkgid:
            self.pkgid = "%s.%s" %(self.name, self.header[rpm.RPMTAG_BUILDTIME])
        self._initRequires()
        self._initProvides()
        self._initConflicts()
        self._initObsoletes()
        self._initFiles()
        self._initDirs()

    def _initPrco(self, nameTag, flagsTag, versionTag):
        names = self.header[nameTag]
        if names is None:
            return []
        flags = self.header[flagsTag]
        flags = map(rpmutils.flagToString, flags)
        vers = self.header[versionTag]
        vers = map(rpmutils.stringToVersion, vers)
        results = []
        for i in range(len(names)):
            results.append((names[i], flags[i], vers[i]))
        return results

    def _initProvides(self):
        nameTag, flagTag, verTag = rpm.RPMTAG_PROVIDENAME,  \
            rpm.RPMTAG_PROVIDEFLAGS, rpm.RPMTAG_PROVIDEVERSION
        self.provides = []
        for elemTuple in self._initPrco(nameTag, flagTag, verTag):
            name, flags, (epoch, ver, rel) = elemTuple
            self.provides.append(Require(name, flags, epoch, ver, rel))

    def _initRequires(self):
        nameTag, flagTag, verTag = rpm.RPMTAG_REQUIRENAME, \
            rpm.RPMTAG_REQUIREFLAGS,rpm.RPMTAG_REQUIREVERSION
        self.requires = []
        for elemTuple in self._initPrco(nameTag, flagTag, verTag):
            name, flags, (epoch, ver, rel) = elemTuple
            self.requires.append(Require(name, flags, epoch, ver, rel))


    def _initConflicts(self):
        nameTag, flagTag, verTag = rpm.RPMTAG_CONFLICTNAME, \
            rpm.RPMTAG_CONFLICTFLAGS, rpm.RPMTAG_CONFLICTVERSION
        self.conflicts = []
        for elemTuple in self._initPrco(nameTag, flagTag, verTag):
            name, flags, (epoch, ver, rel) = elemTuple
            self.conflicts.append(Require(name, flags, epoch, ver, rel))
            
    def _initObsoletes(self):
        nameTag, flagTag, verTag = rpm.RPMTAG_OBSOLETENAME, \
            rpm.RPMTAG_OBSOLETEFLAGS, rpm.RPMTAG_OBSOLETEVERSION
        self.obsoletes = []
        for elemTuple in self._initPrco(nameTag, flagTag, verTag):
            name, flags, (epoch, ver, rel) = elemTuple
            self.obsoletes.append(Require(name, flags, epoch, ver, rel))

    def _initFiles(self):
        self._initFileOrDir('files', rpm.RPMTAG_FILENAMES)

    def _initDirs(self):
        self._initFileOrDir('dirs', rpm.RPMTAG_DIRNAMES)
        
    def _initFileOrDir(self, filetype, tag):
        items = self.header[tag]
        setattr(self, filetype, items)
        
class InstalledRpmPackage(RpmHeaderPackage):
    def __init__(self, header, repo):
        RpmHeaderPackage.__init__(self, header, repo)

    def installed(self):
        return True

    def active(self):
        return True

class LocalRpmPackage(RpmHeaderPackage):
    def __init__(self, fileName):
        self._fileName = fileName

    def init(self):
        repo = FakeRepository(self._fileName)
        header = rpmutils.readRpmHeader(self._fileName)
        if not header:
            return False
        RpmHeaderPackage.__init__(self, header, repo)
        return True

    def getLocation(self):
        return self._fileName

class AinstRpmPackage(RpmHeaderPackage):
    def __init__(self, header, repo, aicfInfo=None):
        RpmHeaderPackage.__init__(self, header, repo)
        self.aicfInfo = aicfInfo

    def installed(self):
        return True

    def active(self):
        return True

if __name__ == '__main__':
    ts = rpm.TransactionSet()
    mi = ts.dbMatch( 'name', 'python' )
    for h in mi:
        headerPackage = RpmHeaderPackage(h, None)
        print headerPackage

        
