#! /usr/bin/python

from package_sack import MultiPackageSack
import time
import re
import fnmatch
from logger import Log

class RepoStorage:
    def __init__(self):
        self.repoDict = {}
        self.packageSack = None
        
    def addRepo(self, repo):
        if self.repoDict.has_key(repo.id):
            return False
        self.repoDict[repo.id] = repo

    def deleteRepo(self, repoid):
        if self.repoDict.has_key(repoid):
            del self.repoDict[repoid]

    def getRepo(self, repoid):
        if self.repoDict.has_key(repoid):
            return self.repoDict[repoid]
        return None

    def enableRepo(self, repoid):
        pattern = re.compile(fnmatch.translate(repoid))
        for key in self.repoDict:
            if pattern.match(key):
                self.repoDict[key].enable()

    def disableRepo(self, repoid):
        pattern = re.compile(fnmatch.translate(repoid))
        for key in self.repoDict:
            if pattern.match(key):
                self.repoDict[key].disable()

    def getEnabledRepo(self):
        repoList = []
        for repo in self.repoDict.values():
            if repo.isEnabled():
                repoList.append(repo)
        repoList.sort()
        return repoList

    def processDisableEnable(self, repos):
        if not repos:
            return True
        for repoItem in repos:
            for key, value in repoItem.items():
                if key == 'disable':
                    self.disableRepo(value)
                elif key == 'enable':
                    self.enableRepo(value)
        return True

    def makeCache(self):
        repoList = self.getEnabledRepo()
        for repo in repoList:
            if not repo.makeCache():
                Log.coutValue(Log.INFO, repo.id, 'failed')
            else:
                Log.coutValue(Log.INFO, repo.id, 'success')
        return True

    def clearCache(self):
        repoList = self.getEnabledRepo()
        for repo in repoList:
            if not repo.clearCache():
                Log.coutValue(Log.INFO, repo.id, 'failed')
                self._consoleLogger.error(log)
            else:
                Log.coutValue(Log.INFO, repo.id, 'success')
        return True

    def getPackageSack(self):
        if not self.packageSack:
            self._initPackageSack()
        return self.packageSack

    def _initPackageSack(self):
        repoList = self.getEnabledRepo()
        self.packageSack = MultiPackageSack()
        for repo in repoList:
            packageSack = repo.getPackageSack()
            if packageSack:
                self.packageSack.addPackageSack(repo.id, packageSack)

    def populateSack(self, metaType):
        packageSack = self.getPackageSack()
        packageSack.populate(metaType)
