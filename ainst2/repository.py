#! /usr/bin/python

class Repository:
    def __init__(self, repoid):
        self.id = repoid
        self.enabled = True
        self.excludeList = []
        self.includeList = []
        self.packageSack = None

    def installed(self):
        return False

    def __cmp__(self, other):
        if self.id > other.id:
            return 1
        elif self.id < other.id:
            return -1
        else:
            return 0

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def isEnabled(self):
        return self.enabled

    def getExcludePkgList(self):
        return self.excludeList

    def getIncludePkgList(self):
        return self.includeList

    def setPackageSack(self, sack):
        self.packageSack = sack

    def getPackageSack(self):
        return self.packageSack

class FakeRepository(Repository):
    def __init__(self, repoid, installed=False):
        Repository.__init__(self, repoid)
        self.enable = True
        self._installed = installed

    def installed(self):
        return self._installed

