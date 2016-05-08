#!/usr/bin/python

try:
    import sqlite3 as sqlite
except ImportError:
    import sqlite
from sqlutils import executeSQL
from package_object import RpmPackageBase, Require, Provide, Conflict, Obsolete

class SqlitePackage(RpmPackageBase):
    def __init__(self, repo=None, name=None, version=None, release=None,
                 epoch = None, arch=None):
        RpmPackageBase.__init__(self, repo, name, version, release, epoch, arch)
        self.checksumType = None
        self.checksumPkgid = None
        self.checksumValue = None
        self.packagesize = None
        self.locationHref = None
        self.obsoletes = []
        self.key = None

    def loadBasic(self, ob):
        self.key = ob['pkgKey']
        self.name = ob['name']
        self.version = ob['version']
        self.release = ob['release']
        self.epoch = ob['epoch']
        self.arch = ob['arch']
        self.checksumType = ob['checksum_type']
        self.checksumPkgid = 'YES'
        self.checksumValue = ob['pkgId']
        self.packagesize = ob['size_package']
        self.locationHref = ob['location_href']

    def addRequires(self, ob):
        r = Require(ob['name'], ob['flags'], ob['epoch'], ob['version'],
                    ob['release'])
        self.requires.append(r)
        
    def addProvides(self, ob):
        r = Provide(ob['name'], ob['flags'], ob['epoch'], ob['version'],
                    ob['release'])
        self.provides.append(r)

    def addConflicts(self, ob):
        r = Conflict(ob['name'], ob['flags'], ob['epoch'], ob['version'],
                    ob['release'])
        self.conflicts.append(r)

    def addObsoletes(self, ob):
        r = Obsolete(ob['name'], ob['flags'], ob['epoch'], ob['version'],
                    ob['release'])
        self.obsoletes.append(r)

    def getLocation(self):
        if self.repo is None or self.locationHref is None:
            return None
        url = self.repo.getBaseUrl()
        if url is None:
            return None
        return url + '/' + self.locationHref

    def printDetail(self):
        print ('==== package %s ====' % self)
        print 'key : ', self.key
        print 'epoch : ', self.epoch
        print 'checksumType : ', self.checksumType
        print 'checksumPkgid : ', self.checksumPkgid
        print 'checksumValue : ', self.checksumValue
        print 'packagesize : ', self.packagesize
        print 'locationHref : ', self.locationHref
        print 'requires : ' , self.requires
        print 'provides : ' , self.provides
        print 'conflicts : ' , self.conflicts
        print 'obsoletes : ' , self.obsoletes


def loadRequires(database, package):
    cur = database.cursor()
    sql = 'select * from requires where pkgKey = ?'
    executeSQL(cur, sql, (package.key,))
    for ob in cur:
        package.addRequires(ob)
    
def loadProvides(database, package):
    cur = database.cursor()
    sql = 'select * from provides where pkgKey = ?'
    executeSQL(cur, sql, (package.key,))
    for ob in cur:
        package.addProvides(ob)
    
def loadConflicts(database, package):
    cur = database.cursor()
    sql = 'select * from conflicts where pkgKey = ?'
    executeSQL(cur, sql, (package.key,))
    for ob in cur:
        package.addConflicts(ob)
    
def loadObsoletes(database, package):
    cur = database.cursor()
    sql = 'select * from obsoletes where pkgKey = ?'
    executeSQL(cur, sql, (package.key,))
    for ob in cur:
        package.addObsoletes(ob)
    
def loadPackages(database):
    cur = database.cursor()
    sql = 'select * from packages'
    executeSQL(cur, sql)
    packages = []
    for ob in cur:
        package = SqlitePackage()
        package.loadBasic(ob)
        loadRequires(database, package)
        loadProvides(database, package)
        loadConflicts(database, package)
        loadObsoletes(database, package)
        packages.append(package)
    return packages
        
def loadFrom(filename):
    if not filename:
        return None
    database = sqlite.connect(filename)
    if sqlite.version_info[0] > 1:
        database.row_factory = sqlite.Row
    return loadPackages(database)

# loadFrom('/home/xide.ql/temp/sqliterpm/primary.sqlite')




