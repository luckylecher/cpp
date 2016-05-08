#! /usr/bin/python

import bsddb
from logger import Log

HASH_DB = 0
BTREE_DB = 1

class BdbWrapper:
    def __init__(self, fileName, dbType=HASH_DB, flag='c', mode=0666):
        self._fileName = fileName
        self._dbType = dbType
        self._flag = flag
        self._mode = mode
        self._db = None

    def open(self):
        if self._db:
            return True
        try:
            if self._dbType == HASH_DB:
                self._db = bsddb.hashopen(self._fileName, self._flag, self._mode)
            elif self._dbType == BTREE_DB:
                self._db = bsddb.btopen(self._fileName, self._flag, self._mode)
            else:
                return False
        except Exception, e:
            Log.cout(Log.ERROR, 'Get db %s failed: %s' % (self._fileName, e))
            self._db = None
            return False
        return True

    def get(self, key):
        if self._db is None:
            return None

        if self._db.has_key(key):
            return self._db[key]
        return None

    def set(self, key, value):
        if self._db is None:
            return False

        self._db[key] = value
        return True

    def setAndReturnOldValue(self, key, value):
        oldValue = None
        if self._db is None:
            return False, oldValue

        if self._db.has_key(key):
            oldValue = self._db[key]
        self._db[key] = value
        return True, oldValue

    def remove(self, key):
        if self._db is None:
            return False

        if self._db.has_key(key):
            del self._db[key]
        return True

    def removeAndReturnOldValue(self, key):
        oldValue = None
        if self._db is None:
            return False, oldValue

        if self._db.has_key(key):
            oldValue = self._db[key]
            del self._db[key]
            return True, oldValue
        return True, oldValue

    def getKeys(self):
        if self._db is None:
            return None
        return self._db.keys()

    def sync(self):
        if self._db is None:
            return False
        self._db.sync()
        return True

    def close(self):
        if self._db is None:
            return False
        self._db.close()
        return True
