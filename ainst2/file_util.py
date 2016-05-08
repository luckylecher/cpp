#! /usr/bin/python

import os
import shutil
import fcntl
from logger import Log

def getAbsPath(path):
    path = os.path.expanduser(path)
    return os.path.abspath(path)

def isFile(path):
    ret = False
    try:
        ret = os.path.isfile(path)
    except Exception, e:
        return False
    return ret

def isDir(path):
    ret = False
    try:
        ret = os.path.isdir(path)
    except Exception, e:
        return False
    return ret

def isLink(path):
    ret = False
    try:
        ret = os.path.islink(path)
    except Exception, e:
        return False
    return ret

def exists(path):
    ret = False
    try:
        ret = os.path.exists(path)
    except Exception, e:
        return False
    return ret

def remove(path):
    try:
        if isLink(path):
            os.remove(path)
        elif isFile(path) and exists(path):
            os.remove(path)
        elif isDir(path):
            shutil.rmtree(path)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Remove %s failed: %s' % (path, e))
        return False
    return True

def rename(src, dest):
    try:
        os.rename(src, dest)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Rename from %s to %s failed: %s' % (src, dest, e))
        return False
    return True

def moveAllSubDir(src, dest):
    try:
        if not isDir(src):
            return False
        ret = os.listdir(src)
        for subDir in ret:
            if not move(src + '/' + subDir, dest + '/' + subDir):
                return False
    except Exception, e:
        Log.cout(Log.DEBUG, 'Move all subdir from %s to %s failed: %s' % (src, dest, e))
        return False
    return True

def move(src, dest):
    try:
        shutil.move(src, dest)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Move %s %s failed: %s' % (src, dest, e))
        return False
    return True

def makeDir(path, clear=False, mode=None):
    try:
        if isDir(path):
            if not clear:
                return True
            else:
                remove(path)
        if mode:
            os.makedirs(path, mode)
        else:
            os.makedirs(path)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Make dir %s failed: %s' % (path, e))
        return False
    return True

def makeDir2(path, clear=False, mode=None):
    mkDirList = []
    if isDir(path):
        return True, mkDirList
    createPath = path
    while path != '':
        path = path.rstrip('/')
        mkDirList.append(path)
        path = os.path.dirname(path)
        if isDir(path):
            break
    return makeDir(createPath, mode), mkDirList

def copyFile(srcFile, destFile):
    try:
        shutil.copy(srcFile, destFile)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Copy %s %s failed: %s' % (srcFile, destFile, e))
        return False
    return True

def listDir(dirPath):
    dirs = []
    if not isDir(dirPath):
        Log.cout(Log.DEBUG, 'List dir %s failed' % dirPath)
        return None
    try:
        dirs = os.listdir(dirPath)
    except Exception, e:
        Log.cout(Log.DEBUG, 'List dir %s failed: %s' % (dirPath, e))
        return None
    return dirs

def link(src, dst):
    try:
        os.link(src, dst)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Link %s %s failed: %s' % (src, dst, e))
        return False
    return True

def symLink(src, dst):
    try:
        os.symlink(src, dst)
    except Exception, e:
        Log.cout(Log.DEBUG, 'symLink %s %s failed: %s' % (src, dst, e))
        return False
    return True

def readLink(path):
    try:
        if isLink(path):
            return os.readlink(path)
    except Exception, e:
        Log.cout(Log.DEBUG, 'readlink %s failed: %s' % (path, e))
        return None
    return None

def writeToFile(fileName, content, flags='w', mode=0777):
    fout = None
    try:
        fout = open(fileName, flags, mode)
        fout.write(content)
    except Exception, e:
        if fout in locals():
            fout.close()
        Log.cout(Log.DEBUG, 'Write to %s failed: %s' % (fileName, e))
        return False
    fout.close()
    return True

def writeToFp(fp, content):
    try:
        fp.write(content)
        fp.flush()
    except Exception, e:
        Log.cout(Log.DEBUG, 'Write to fp failed: %s' % e)
        return False
    return True

def readFromFile(fileName):
    fin = None
    content = None
    try:
        fin = open(fileName)
        content = fin.read()
    except Exception, e:
        Log.cout(Log.DEBUG, 'Read from %s failed: %s' % (fileName, e))
        if fin in locals():
            fin.close()
        return None
    fin.close()
    return content

def chmod(path, perm):
    try:
        os.chmod(path, perm)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Chmod %s failed: %s' % (path, e))
        return False
    return True

def lockFp(fp):
    try:
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Lock failed: %s' % e)
        return False
    return True

def unlockFp(fp):
    try:
        fcntl.flock(fp, fcntl.LOCK_UN)
    except Exception, e:
        Log.cout(Log.DEBUG, 'Unlock failed: %s' % e)
        return False
    return True

def getFp(filePath, flags, mode=0777):
    try:
        fp = open(filePath, flags, mode)
        return fp
    except Exception, e:
        Log.cout(Log.DEBUG, 'Open file %s failed: %s' %(filePath, e))
    return None

if __name__ == '__main__':
    pass
