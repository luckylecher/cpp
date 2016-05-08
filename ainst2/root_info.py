#! /usr/bin/python

import os
from logger import Log
import file_util
from bdb_wrapper import BdbWrapper

class RootInfo:
    def __init__(self):
        self.installRootSet = set()

class RootInfoStreamer:
    def load(self, path):
        return None

    def dump(self, rootInfo, path):
        return False

class RootInfoFileStreamer(RootInfoStreamer):
    def load(self, path):
        if not file_util.isFile(path):
            Log.cout(Log.DEBUG, 'Root info file %s is not exists' % path)
            return RootInfo()
        content = file_util.readFromFile(path)
        if content is None:
            Log.cout(Log.ERROR, 'Read root info file %s failed' % path)
            return None

        rootInfo = RootInfo()
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            rootInfo.installRootSet.add(line)
        return rootInfo

    def dump(self, rootInfo, path):
        content = ''
        for installRoot in rootInfo.installRootSet:
            content += installRoot + '\n'
        preUmask = os.umask(0)
        ret = file_util.writeToFile(path, content)
        os.umask(preUmask)
        if not ret:
            Log.cout(Log.ERROR, 'Dump to [%s] failed' % path)
        return ret

class RootInfoDbStreamer(RootInfoStreamer):
    def load(self, path):
        rootInfoDb = self._getDb(path)
        if not rootInfoDb:
            Log.cout(Log.ERROR, 'Get root info db failed')
            return None

        rootInfo = RootInfo()
        rootInfo.installRootSet = set(rootInfoDb.getKeys())
        rootInfoDb.close()
        return rootInfo

    def dump(self, rootInfo, path):
        rootInfoDb = self._getDb(path)
        if not rootInfoDb:
            Log.cout(Log.ERROR, 'Get root info db failed')
            return False
        for key in rootInfoDb.getKeys():
            if key not in rootInfo.installRootSet:
                rootInfoDb.remove(key)

        dbKeys = rootInfoDb.getKeys()
        for installRoot in rootInfo.installRootSet:
            if installRoot not in dbKeys:
                rootInfoDb.set(installRoot, '1')
        rootInfoDb.sync()
        rootInfoDb.close()
        return True

    def _getDb(self, path):
        preUmask = os.umask(0)
        rootInfoDb = BdbWrapper(path)
        if not rootInfoDb.open():
            return None
        os.umask(preUmask)
        return rootInfoDb
