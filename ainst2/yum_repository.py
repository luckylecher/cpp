#! /usr/bin/python
import time
from logger import Log
from repository import Repository
from package_sack import PackageSack
from cache_handler import *

class YumRepository(Repository):
    def __init__(self, repoid, repoConfig, maxFileLength=1024*1024*1024*2,
                 retryTime=3, socketTimeout=5):
        Repository.__init__(self, repoid)
        self.repoConfig = repoConfig
        self.cachedir = None
        self.expireTime = None
        self.enabled = bool(repoConfig.enabled)
        self.maxFileLength = maxFileLength
        self.retryTime = retryTime
        self.socketTimeout = socketTimeout

    def getBaseUrl(self):
        return self.repoConfig.baseurl

    def makeCache(self):
        cacheHandler = RepoCacheHandler(self.id, self.repoConfig, 
                                        self.cachedir, self.expireTime,
                                        self.maxFileLength, self.retryTime,
                                        self.socketTimeout)
        if not cacheHandler.makeCache(force=True):
            return False
        return True

    def clearCache(self):
        cacheHandler = RepoCacheHandler(self.id, self.repoConfig, 
                                        self.cachedir, self.expireTime,
                                        self.maxFileLength, self.retryTime,
                                        self.socketTimeout)
        return cacheHandler.clearCache()
        
    def getPackageSack(self):
        if self.packageSack is None:
            self._initPackageSack()
        return self.packageSack
        
    def _initPackageSack(self):
        cacheHandler = RepoCacheHandler(self.id, self.repoConfig, 
                                        self.cachedir, self.expireTime,
                                        self.maxFileLength, self.retryTime,
                                        self.socketTimeout)
        pkgList = cacheHandler.getMetaData()
        if pkgList is None:
            self.packageSack = None
            return None
        self.packageSack = PackageSack()
        for pkg in pkgList:
            pkg.repo = self
            self.packageSack.addPackageObject(pkg)

        self.packageSack.buildIndex()

if __name__ == "__main__":
    repoConfig = RepoConfigItem()
    repoConfig.baseurl = "http://10.250.8.21/repos/release/"
    repo = YumRepository("search_release", repoConfig)
    repo.cachedir = "./cache/"
    repo.expireTime = 10
    start = time.time()
    sack = repo.getPackageSack()
    end = time.time()
    print "Total Cost: %d ms" % ((end - start) * 1000)

    start = time.time()
    result = sack.searchPkg("anet")
    end = time.time()
    #print "Search one pkg  cost: %d ms" % ((end - start) * 1000)
    #print result

    start = time.time()
    result = sack.searchPkg("aggregator", release="rc_2")
    end = time.time()
    #print "Search one pkg  cost: %d ms" % ((end - start) * 1000)
    #print result
