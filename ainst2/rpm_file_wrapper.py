#! /usr/bin/python

import rpm
import stat
import rpmutils
import file_util
from logger import Log
from rpm_header_reader import FileFlags, RpmHeaderReader


class RpmFileInfo:
    def __init__(self, baseName='', isDir=False, relativePath='',
                 fileFlag=FileFlags.RPMFILE_NONE):
        self.fileFlag = fileFlag
        self.baseName = baseName
        self.isDir = isDir
        self.relativePath = relativePath

    def isConfigFile(self):
        if self.fileFlag & FileFlags.RPMFILE_CONFIG:
            return True
        return False

    def __eq__(self, info):
        return self.fileFlag == info.fileFlag and \
               self.baseName == info.baseName and \
               self.isDir == info.isDir and \
               self.relativePath == info.relativePath


class RpmFileWrapper:
    def convert(self, rpmFilePath):
        if not file_util.isFile(rpmFilePath):
            Log.cout(Log.ERROR, 'Rpm file [%s] not existed' % rpmFilePath)
            return None
        rpmHeader = rpmutils.readRpmHeader(rpmFilePath)
        if rpmHeader is None:
            Log.cout(Log.ERROR, 'Read rpm header failed: [%s]' % rpmFilePath)
            return None
        rpmHeaderReader = RpmHeaderReader(rpmHeader)
        fileList = rpmHeaderReader.getFiles()
        rpmFileInfoList = []
        if len(fileList) == 0:
            Log.cout(Log.INFO, 'Rpm filelist has no file')
            return rpmFileInfoList

        firstPath = rpmHeaderReader.getDirNameByIndex(fileList[0][2]) + fileList[0][1]
        if stat.S_ISDIR(fileList[0][3]):
            firstPath += '/'

        for fileObj in fileList:
            dirName = rpmHeaderReader.getDirNameByIndex(fileObj[2])
            path = dirName + fileObj[1]
            isDir = stat.S_ISDIR(fileObj[3])
            if isDir:
                path = path + '/'
            if not path.startswith('/'):
                Log.cout(Log.ERROR, 'Rpm file has illegal prefix: %s' % path)
                return None
            path = path[len('/'):]
            if (path == '' or path.startswith('ainst/')
                or path.startswith('usr/ainst/')
                or path.startswith('usr/local/ainst/')):
                continue
            rpmFileInfo = RpmFileInfo(fileObj[1], isDir, path, fileObj[0])
            rpmFileInfoList.append(rpmFileInfo)
        return rpmFileInfoList


if __name__ == '__main__':
    rpmPath0 = '/home/xiaoming.zhang/aicf/aggregator/build/release64/rpm_build/RPMS/x86_64/aggregator-3.9.1-rc_1.x86_64.rpm'
    rpmPath1 = '/home/xiaoming.zhang/libredis-0.1.0-rc_1.x86_64.rpm'
    rpmPath2 = '/home/xiaoming.zhang/xx/var/ainst/tmp/zookeeper-client-devel-3.3.5-rc_2.x86_64.rpm'
    rpmPath3 = '/home/xiaoming.zhang/xx/var/ainst/tmp/amonitor-0.1.3-rc_2.x86_64.rpm'
    rpmPath4 = '/home/xiaoming.zhang/xx/var/ainst/tmp/apsara-sdk-0.10.1-rc_3.x86_64.rpm'
    rpmPath5 = '/tmp/libredis-0.1.0-rc_1.x86_64.rpm'
    rpmPathList = [rpmPath5]
    for rpmPath in rpmPathList:
        rpmInfoList = RpmFileWrapper().convert(rpmPath)
        print rpmPath
        for rpmInfo in rpmInfoList:
            print 'relativeName', rpmInfo.relativePath
            print 'isDir', rpmInfo.isDir
            print 'baseName', rpmInfo.baseName
