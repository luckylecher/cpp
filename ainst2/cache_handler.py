#! /usr/bin/python

import cache
import os,time,sha,md5
from logger import Log
import gzip
import bz2
import file_util
from ainst_config import RepoConfigItem
from file_fetcher import FileFetcher
from repomd_parser import RepoMdParser
import sqlite_loader

PRIMARY_TYPE=1
PRIMARYDB_TYPE=2
ALL_TYPE=3

PRIMARY_NAME = 'primary'
PRIMARYDB_NAME = 'primary_db'

PRIMARY_FILE = 'primary.xml'
PRIMARYDB_FILE = 'primary.sqlite'

class RepoCacheHandler:
    def __init__(self, repoid, repoConfig, cacheDir, expireTime,
                 maxFileLength=1024*1024*1024*2, retryTime=3, socketTimeout=5):
        self.repoid = repoid
        self.repoConfig = repoConfig
        self.cacheDir = cacheDir
        self.expireTime = expireTime
        self.repomdLocation = '/repodata/repomd.xml'
        self.repoDataDir = None
        self.packageCacheDir = '/packages/'
        self.fileFetcher = FileFetcher(socketTimeout, retryTime, maxFileLength)

    def getPackage(self, pkg):
        if self._getRepoDataDir() is None:
            return None
        pkgCacheDir = self._getRepoDataDir() + self.packageCacheDir
        preUmask = os.umask(0)
        if not file_util.makeDir(pkgCacheDir):
            os.umask(preUmask)
            Log.cout(Log.ERROR, 'Make cache dir [%s] failed' % pkgCacheDir)
            return None
        os.umask(preUmask)
        uri = pkg.getLocation()
        if not uri.lower().startswith('http'):
            return None
        pkgFilePath = pkgCacheDir + os.path.basename(uri)
        if file_util.exists(pkgFilePath):
            ctime = os.stat(pkgFilePath).st_ctime
            nowtime = time.time()
            if nowtime - ctime < self.expireTime:
                Log.cout(Log.DEBUG, "Get package [%s] from cache" % pkg)
                return pkgFilePath
            if not file_util.remove(pkgFilePath):
                Log.cout(Log.DEBUG, "Remove old package [%s] because of expired" % pkg)
                return None
                
        if not self.fileFetcher.fetch(uri, pkgFilePath) or \
                not file_util.chmod(pkgFilePath, 0666):
            return None
        return pkgFilePath

    def makeCache(self, metatype=PRIMARY_TYPE, force=False):
        if self._getRepoDataDir() is None:
            return False
        needCache = False
        cacheType = None
        if force is True:
            needCache = True
            cacheType = metatype
        else:
            (needCache, cacheType) = self._needMakeCache(metatype)
        if needCache is False:
            Log.cout(Log.INFO, 'Need not update cache: %s' % self.repoid)
            return True
        ret = False
        Log.cout(Log.INFO, 'Need update cache: %s' % self.repoid)
        if self._doMakeCache(cacheType):
            ret = self._onMakeCacheSuccess(cacheType)
        else:
            self._onMakeCacheFailed(cacheType)
        return ret

    def clearCache(self):
        return file_util.remove(self._getRepoDataDir())

    def getMetaData(self):
        if not self.makeCache(ALL_TYPE):
            Log.cout(Log.ERROR, 'Make cache failed: %s' % self.repoid)
            return None
        if file_util.exists(self._getRepoDataDir() + '/' + PRIMARYDB_FILE):
            Log.cout(Log.INFO, 'Using primatydb format: %s' % self.repoid)
            return sqlite_loader.loadFrom(self._getRepoDataDir() +
                                          '/' + PRIMARYDB_FILE)
        elif file_util.exists(self._getRepoDataDir() + '/' + PRIMARY_FILE):
            Log.cout(Log.INFO, 'Using primaty format: %s' % self.repoid)
            return cache.loadFromFile(self._getRepoDataDir() +
                                      '/' + PRIMARY_FILE)
        Log.cout(Log.ERROR, 'repodb not found: %s' % self.repoid)
        return None
        

    def _filterMetaTypeByRepoMD(self, metatype, repoMdObj):
        hasPrimary = repoMdObj.repoMdDatas.has_key(PRIMARY_NAME)
        hasPrimaryDB = repoMdObj.repoMdDatas.has_key(PRIMARYDB_NAME)
        if metatype == ALL_TYPE:
            if not hasPrimaryDB:
                return PRIMARY_TYPE
            elif not hasPrimary:
                return PRIMARYDB_TYPE
        return metatype
    
    def _doMakeCache(self, metatype):
        #download repomd.xml to repomd.xml.tmp
        repomdTmpFile = self._getRepoDataDir() + '/' + \
            self.repomdLocation.split('/')[-1] + ".tmp"
        repomdUrl = self.repoConfig.baseurl + self.repomdLocation
        if not file_util.remove(repomdTmpFile) or \
                not self.fileFetcher.fetch(repomdUrl, repomdTmpFile) or\
                not file_util.chmod(repomdTmpFile, 0666):
            return False
        repoMdObj = RepoMdParser().parse(repomdTmpFile)
        if not repoMdObj:
            return False
        metatype = self._filterMetaTypeByRepoMD(metatype, repoMdObj)
        if metatype == PRIMARY_TYPE:
            return self._getMetaFile(repoMdObj, PRIMARY_NAME, PRIMARY_FILE)
        elif metatype == PRIMARYDB_TYPE:
            return self._getMetaFile(repoMdObj, PRIMARYDB_NAME, PRIMARYDB_FILE)
        elif metatype == ALL_TYPE:
            return self._getMetaFile(repoMdObj, PRIMARY_NAME, PRIMARY_FILE) and \
                self._getMetaFile(repoMdObj, PRIMARYDB_NAME, PRIMARYDB_FILE)
        else:
            return False

    def _getMetaFile(self, repoMdObj, metaName, fileName):
        if not repoMdObj.repoMdDatas.has_key(metaName):
            return False
        metaObj = repoMdObj.repoMdDatas[metaName]
        destTmpFile = self._getRepoDataDir() + '/' + \
            metaObj.locationHref.split('/')[-1]
        metaUrl = self.repoConfig.baseurl + '/' + metaObj.locationHref
#        uncompressTmpFile = '.'.join(destTmpFile.split('.')[:-1]) + '.tmp'
        uncompressTmpFile = self._getRepoDataDir() + '/' + \
            fileName + '.tmp'
        if not file_util.remove(destTmpFile) or\
                not file_util.remove(uncompressTmpFile):
            return False
        if not self.fileFetcher.fetch(metaUrl, destTmpFile) or\
                not file_util.chmod(destTmpFile, 0666):
            return False
        try:
            if destTmpFile.split('.')[-1] == 'bz2':
                f = bz2.BZ2File(destTmpFile)
            else:
                f = gzip.open(destTmpFile)
            if not file_util.writeToFile(uncompressTmpFile, f.read()) or\
                    not file_util.chmod(uncompressTmpFile, 0666):
                f.close()
                return False
            f.close()
        except Exception:
            Log.cout(Log.ERROR, 'decompress %s failed' % destTmpFile)
            return False
        return self._checkSumValid(metaObj, uncompressTmpFile)
    
    def _needMakeCache(self, metatype):
        #check cachecookie
        cachecookie = self._getRepoDataDir() + '/' + 'cachecookie';
        if not file_util.exists(cachecookie):
            return (True, metatype)
        ctime = os.stat(cachecookie).st_ctime
        nowtime = time.time()
        if nowtime - ctime > self.expireTime:
            return (True, metatype)
        #check repomd.xml
        repomdFile = self._getRepoDataDir() + '/' + self.repomdLocation.split('/')[-1]
        if not file_util.exists(repomdFile):
            return (True, metatype)
        mdParser = RepoMdParser()
        repoMd = mdParser.parse(repomdFile)
        if repoMd is None:
            return (True, metatype)
        metatype = self._filterMetaTypeByRepoMD(metatype, repoMd)
        #check metatype
        if metatype == PRIMARY_TYPE:
            if not self._checkMetaFile(repoMd, PRIMARY_NAME, PRIMARY_FILE):
                return (True, metatype)
        elif metatype == PRIMARYDB_TYPE:
            if not self._checkMetaFile(repoMd, PRIMARYDB_NAME, PRIMARYDB_FILE):
                return (True, metatype)
        elif metatype == ALL_TYPE:
            primaryRet = self._checkMetaFile(repoMd, PRIMARY_NAME, PRIMARY_FILE)
            primarydbRet = self._checkMetaFile(repoMd,
                                               PRIMARYDB_NAME, PRIMARYDB_FILE)
            if primaryRet and not primarydbRet:
                return (True, PRIMARYDB_TYPE)
            elif not primaryRet and primarydbRet:
                return (True, PRIMARY_TYPE)
            elif not primaryRet and not primarydbRet:
                return (True, ALL_TYPE)
        return (False, None)

    def _checkMetaFile(self, repoMd, metaName, fileName):
        metaFile = self._getRepoDataDir() + '/' + fileName
        if not file_util.exists(metaFile):
            return False
        if not repoMd.repoMdDatas.has_key(metaName):
            Log.cout(Log.ERROR, '%s not found in repomd.xml' % metaName)
            return False
        metaObj = repoMd.repoMdDatas[metaName]
        return self._checkSumValid(metaObj, metaFile)

    def _onMakeCacheSuccess(self, cacheType):
        cachecookie = self._getRepoDataDir() + '/' + 'cachecookie';
        if not file_util.remove(cachecookie) or\
                not file_util.writeToFile(cachecookie, '') or\
                not file_util.chmod(cachecookie, 0666):
            Log.cout(Log.ERROR, 'Re-touch cachecookie failed')
            return False
        repomdTmpFile = self._getRepoDataDir() + '/' + \
            self.repomdLocation.split('/')[-1];
        if not file_util.rename(repomdTmpFile + '.tmp', repomdTmpFile):
            return False
        return self._processTmpFile(cacheType, True)

    def _onMakeCacheFailed(self, cacheType):
        repomdTmpFile = self._getRepoDataDir() + '/' + \
            self.repomdLocation.split('/')[-1];
        if not file_util.remove(repomdTmpFile + '.tmp'):
            return False
        return self._processTmpFile(cacheType, False)

    def _processTmpFile(self, cacheType, success):
        nameList = []
        if cacheType == PRIMARY_TYPE:
            nameList.append(PRIMARY_FILE)
        elif cacheType == PRIMARYDB_TYPE:
            nameList.append(PRIMARYDB_FILE)
        elif cacheType == ALL_TYPE:
            nameList.append(PRIMARY_FILE)
            nameList.append(PRIMARYDB_FILE)
        for name in nameList:
            fileName = self._getRepoDataDir() + '/' + name
            if not file_util.exists(fileName + '.tmp'):
                continue
            if success:
                if not file_util.rename(fileName + '.tmp', fileName):
                    return False
            else:
                if not file_util.remove(fileName + '.tmp'):
                    return False
            if not file_util.remove(fileName + '.gz'):
                return False
        return True

    def _getRepoDataDir(self):
        if self.repoDataDir:
            return self.repoDataDir
        if not self.cacheDir or not self.repoid:
            return None
        self.repoDataDir = self.cacheDir + '/' + self.repoid
        if not file_util.exists(self.repoDataDir):
            preUmask = os.umask(0)
            ret = file_util.makeDir(self.repoDataDir, True, 0777)
            os.umask(preUmask)
            if not ret: 
                Log.cout(Log.ERROR, 'make repo data dir %s failed' % self.repoDataDir)
                return None
        return self.repoDataDir

    def _checkSumValid(self, metaObj, filePath):
        if metaObj.openchecksumType == "sha":
            return  self._sha1(filePath) == metaObj.openchecksumValue
        elif metaObj.openchecksumType == "md5":
            return  self._md5(filePath) == metaObj.openchecksumValue
        return False

    def _md5(self, filePath):
        f = open(filePath,'rb')
        md5Obj = md5.new()
        md5Obj.update(f.read())
        f.close()
        return md5Obj.hexdigest()
        
    def _sha1(self, filePath):
        f = open(filePath,'rb')
        shaObj = sha.new()
        shaObj.update(f.read())
        f.close()
        return shaObj.hexdigest()

if __name__ == "__main__":
    handler = RepoCacheHandler('apsara', None, '/var/ainst/cache/', 3600)
    handler.getPackage('aa')
    a = '''
    repoConfig = RepoConfigItem()
    repoConfig.baseurl = "http://10.250.8.21/repos/release/"
    handler = RepoCacheHandler('larmmi', repoConfig, "./cache/", 10000)

    start = time.time()
    handler.clearCache()
    end = time.time()
    print "Clear Cache Cost %d ms" % ((end - start) * 1000)
    start = time.time()
    handler = RepoCacheHandler('larmmi', repoConfig, "./cache/", 10000)
    handler.makeCache(PRIMARY_TYPE)
    end = time.time()
    print "Make Cache Cost %d ms" % ((end - start) * 1000)

    start = time.time()
    handler = RepoCacheHandler('larmmi', repoConfig, "./cache/", 10000)
    pkgList = handler.getMetaData()
    end = time.time()
    print "Get Pkg List Cost %d ms" % ((end - start) * 1000)
'''
