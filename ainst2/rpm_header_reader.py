#!/usr/bin/python

import rpm
from logger import Log

class FileFlags:
    RPMFILE_NONE = 0
    RPMFILE_CONFIG = 1 << 0
    RPMFILE_DOC = 1 << 1
    RPMFILE_DONOTUSE = 1 << 2
    RPMFILE_MISSINGOK = 1 << 3
    RPMFILE_NOREPLACE = 1 << 4
    RPMFILE_SPECFILE = 1 << 5
    RPMFILE_GHOST = 1 << 6
    RPMFILE_LICENSE = 1 << 7
    RPMFILE_README = 1 << 8
    RPMFILE_EXCLUDE = 1 << 9

class RpmHeaderReader:
    HEADERTAG_MAP = {'name' : rpm.RPMTAG_NAME,
                   'version' : rpm.RPMTAG_VERSION,
                   'release' : rpm.RPMTAG_RELEASE,
                   'summary' : rpm.RPMTAG_SUMMARY,
                   'description' : rpm.RPMTAG_DESCRIPTION,
                   'buildtime' : rpm.RPMTAG_BUILDTIME,
                   'buildhost' : rpm.RPMTAG_BUILDHOST,
                   'size' : rpm.RPMTAG_SIZE,
                   'license' : rpm.RPMTAG_LICENSE,
                   'group' : rpm.RPMTAG_GROUP,
                   'os' : rpm.RPMTAG_OS,
                   'arch' : rpm.RPMTAG_ARCH,
                   'sourcerpm' : rpm.RPMTAG_SOURCERPM,
                   'fileverifyflags' : rpm.RPMTAG_FILEVERIFYFLAGS,
                   'archivesize' : rpm.RPMTAG_ARCHIVESIZE,
                   'rpmversion' : rpm.RPMTAG_RPMVERSION,
                   'changelogtime' : rpm.RPMTAG_CHANGELOGTIME,
                   'changelogname' : rpm.RPMTAG_CHANGELOGNAME,
                   'changelogtext' : rpm.RPMTAG_CHANGELOGTEXT,
                   'cookie' : rpm.RPMTAG_COOKIE,
                   'optflags' : rpm.RPMTAG_OPTFLAGS,
                   'payloadformat' : rpm.RPMTAG_PAYLOADFORMAT,
                   'payloadcompressor' : rpm.RPMTAG_PAYLOADCOMPRESSOR,
                   'payloadflags' : rpm.RPMTAG_PAYLOADFLAGS,
                   'rhnplatform' : rpm.RPMTAG_RHNPLATFORM,
                   'platform' : rpm.RPMTAG_PLATFORM}

    def __init__(self, header):
        self._header = header
        self._fileList = None
        self._dirList = None

    def getInfoByName(self, name):
        if not self._header:
            return None
        if RpmHeaderReader.HEADERTAG_MAP.has_key(name):
            return self._header[RpmHeaderReader.HEADERTAG_MAP[name]]
        return None

    def getFiles(self):
        if self._fileList is not None:
            return self._fileList
        if not self._header:
            return []
        self._fileList = []
        dirList = self._getDirs()
        fileFlagList = []
        if type(self._header[rpm.RPMTAG_FILEFLAGS]) is list:
            fileFlagList = self._header[rpm.RPMTAG_FILEFLAGS]
        else:
            fileFlagList.append(self._header[rpm.RPMTAG_FILEFLAGS])
        baseNameList = []
        if type(self._header[rpm.RPMTAG_BASENAMES]) is list:
            baseNameList = self._header[rpm.RPMTAG_BASENAMES]
        else:
            baseNameList.append(self._header[rpm.RPMTAG_BASENAMES])
        dirIndexList = []
        if type(self._header[rpm.RPMTAG_DIRINDEXES]) is list:
            dirIndexList = self._header[rpm.RPMTAG_DIRINDEXES]
        else:
            dirIndexList.append(self._header[rpm.RPMTAG_DIRINDEXES]) 
        fileModeList = []
        if type(self._header[rpm.RPMTAG_FILEMODES]) is list:
            fileModeList = self._header[rpm.RPMTAG_FILEMODES]
        else:
            fileModeList.append(self._header[rpm.RPMTAG_FILEMODES]) 

        try:
            self._fileList = zip(fileFlagList,
                           baseNameList,
                           dirIndexList,
                           fileModeList)
        except:
            Log.cout(Log.ERROR, 'Get files from rpm header failed')
            return None
        return self._fileList

    def getDirNameByIndex(self, index):
        if not self._header:
            Log.cout(Log.ERROR, 'Get dir name failed')
            return None            
        dirListLength = len(self._getDirs())
        if index > dirListLength:
            Log.cout(Log.ERROR, 'Get dir name failed')
            return None
        return self._getDirs()[index]
    
    def _getDirs(self):
        if self._dirList is None:
            self._dirList = self._header[rpm.RPMTAG_DIRNAMES]
        return self._dirList

if __name__ == '__main__':
    import rpmutils
    ts = rpm.TransactionSet()
    path = '/home/xiaoming.zhang/aicf/aggregator/build/release64/rpm_build/RPMS/x86_64/aggregator-3.9.1-rc_1.x86_64.rpm'
    path = '/home/xiaoming.zhang/xx/var/ainst/tmp/amonitor-0.1.3-rc_2.x86_64.rpm'
    header = rpmutils.readRpmHeader(ts, path)
    reader = RpmHeaderReader(header)
    print reader.getInfoByName('name')
    print reader.getInfoByName('version')
    print reader.getInfoByName('release')
    print reader.getInfoByName('summary')
    print reader.getInfoByName('description')
    print reader.getInfoByName('buildtime')
    print reader.getInfoByName('buildhost')
    print reader.getInfoByName('size')
    print reader.getInfoByName('license')
    print reader.getInfoByName('group')
    print reader.getInfoByName('os')
    print reader.getInfoByName('arch')
    print reader.getInfoByName('sourcerpm')
    print reader.getInfoByName('fileverifyflags')
    print reader.getInfoByName('archivesize')
    print reader.getInfoByName('rpmversion')
    print reader.getInfoByName('changelogtime')
    print reader.getInfoByName('changelogname')
    print reader.getInfoByName('changelogtext')
    print reader.getInfoByName('cookie')
    print reader.getInfoByName('optflags')
    print reader.getInfoByName('payloadformat')
    print reader.getInfoByName('payloadcompressor')
    print reader.getInfoByName('payloadflags')
    print reader.getInfoByName('rhnplatform')
    print reader.getInfoByName('platform')

    print "\n\n"
    fileList = reader.getFiles()
    for item in fileList:
        import stat
        if stat.S_ISDIR(int(item[3])):
            print item

        

    print "\n\n"
    print reader._getDirs()

