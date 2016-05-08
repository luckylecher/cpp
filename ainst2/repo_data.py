#! /usr/bin/python

class RepoMdData:
    def __init__(self):
        self.type = None
        self.locationHref = None
        self.checksumType = None
        self.checksumValue = None
        self.timestamp = None
        self.openchecksumType = None
        self.openchecksumValue = None

class RepoMd:
    def __init__(self):
        self.repoMdDatas = {}


class PackagePrimary:
    def __init__(self):
        self.name = None
        self.arch = None
        self.epoch = None
        self.ver = None
        self.rel = None
        self.checksumType = None
        self.checksumValue = None
        self.checksumPkgid = None
        self.packageSize = None
        self.locationHref = None
        #tuple: name, flags, epoch, ver, rel
        self.requireTuples = []
        self.provideTuples = []
        self.conflictTuples = []
        self.obsoleteTuples = []
        
class RepoPrimary:
    def __init__(self):
        self.packages = []

class PackageFilelists:
    def __init__(self):
        self.pkgidValue = None
        self.name = None
        self.arch = None
        self.epoch = None
        self.ver = None
        self.rel = None
        self.fileList = []
        self.dirList = []

class RepoFilelists:
    def __init__(self):
        self.packages = {}


class RepoData:
    def __init__(self):
        self.repoPrimary = None
        self.repoFilelists = None
