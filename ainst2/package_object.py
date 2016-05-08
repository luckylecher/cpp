#! /usr/bin/python 

class Require:
    def __init__(self, name=None, flags=None, epoch=None, 
                 version=None, release=None):
        self.name = name
        self.flags = flags
        self.epoch = epoch
        self.version = version
        self.release = release
    
    def getTuple(self):
        return (self.name, self.flags, (self.epoch, self.version, self.release))

    def __str__(self):
        version = self.version
        if self.epoch != None and self.epoch != '0':
            version = '%s:%s' % (self.epoch, version)
        if self.release is not None:
            version = '%s-%s' % (version, self.release)
        return '%s %s %s' % (self.name, self.flags, version)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return self.getTuple().__hash__()

class Provide(Require):
    def __init__(self, name=None, flags=None,
                 epoch=None,version=None, release= None):
        Require.__init__(self, name, flags, epoch, version, release)

class Conflict(Require):
    def __init__(self, name=None, flags=None,
                 epoch=None,version=None, release= None):
        Require.__init__(self, name, flags, epoch, version, release)

class Obsolete(Require):
    def __init__(self, name=None, flags=None,
                 epoch=None,version=None, release= None):
        Require.__init__(self, name, flags, epoch, version, release)

class PackageObject:
    def __init__(self, name=None, version=None, release=None,
                 epoch = None, arch=None):
        self.name = name
        self.version = version
        self.release = release
        self.epoch = epoch
        self.arch = arch
        self.requires = []
        self.provides = []
        self.conflicts = []

    def getTuple(self):
        return (self.name, self.epoch, self.version, self.release, self.arch)

    def __str__(self):
        ret = '%s-%s-%s.%s' % (self.name, self.version, self.release,
                               self.arch)        
        if self.epoch != None and str(self.epoch) != '0':
            ret = '%s:' % str(self.epoch) + ret
        return ret

    def __repr__(self):
        return self.__str__()

    def installed(self):
        return False

class RpmPackageBase(PackageObject):
    def __init__(self, repo=None, name=None, version=None, release=None,
                 epoch = None, arch=None):
        PackageObject.__init__(self, name, version, release, epoch, arch)
        self.repo = repo
        self.obsoletes = []
        self.files= []
        self.dirs = []
        self.ghosts = []
        self.summary = None
        self.description = None
        self.packagesize = None

class FakeAinstLocalInstallPackage(RpmPackageBase):
    def __init__(self, repository, pkg):
        RpmPackageBase.__init__(self, repo=repository, name=pkg.name,
                                version=pkg.version, release=pkg.release,
                                epoch=pkg.epoch, arch=pkg.arch)
        self.requires = pkg.requires
        self.provides = pkg.provides
        self.conflicts = pkg.conflicts
        self.obsoletes = pkg.obsoletes

    def installed(self):
        return True

if __name__ == "__main__":
    pkg = PackageObject(name="larmmi", version="vivian")
    print pkg
