#! /usr/bin/python

import re

class CrontabInfo:
    def __init__(self):
        self.crontabDict = {}

class CrontabInfoStreamer:
    def __init__(self):
        self._begin = '#@@ainst.begin@@\n'
        self._installRootPrefix = '#ainst.installroot:'
        self._packagePrefix = '#ainst.package:'
        self._end = '#@@ainst.end@@\n'

    def parseCrontabInfo(self, content):
        crontabInfo = CrontabInfo()
        if not content:
            return crontabInfo
        pattern = re.compile(self._begin + '.*?' + self._end, re.S)
        infos = pattern.findall(content)
        if not infos:
            return crontabInfo

        for info in infos:
            patternString = self._begin + self._installRootPrefix +\
                '([^\n]+)\n'+ self._packagePrefix + '([^\n]+)\n(.*)' +\
                self._end
            pattern = re.compile(patternString, re.S)
            match = pattern.match(info)
            if match:
                installRoot = match.group(1)
                pkgName = match.group(2)
                installRoot = installRoot.strip()
                pkgName = pkgName.strip()
                if not installRoot or not pkgName:
                    continue
                crontabInfo.crontabDict[(installRoot, pkgName)] = match.group(3)
        return crontabInfo

    def addCrontabItem(self, crontabString, installRoot, pkgName, content):
        crontabString += '\n' + self._makeCrontabString(installRoot,
                                                       pkgName, content) + '\n'
        return crontabString

    def cutCrontabItem(self, crontabString, installRoot, pkgName):
        patternString = self._begin + self._installRootPrefix +\
            installRoot + '\n'+ self._packagePrefix + pkgName +\
            '\n.*?' + self._end
        pattern = re.compile(patternString, re.S)
        crontabString, subCount = pattern.subn('', crontabString)        
        return crontabString

    def buildCrontabString(self, crontabInfo):
        content = ''
        if not crontabInfo or not crontabInfo.crontabDict:
            return content
        for installRoot, pkgName in crontabInfo.crontabDict:
            pkgCrobtab = crontabInfo.crontabDict[(installRoot, pkgName)]
            content += self._makeCrontabString(installRoot, pkgName,
                                               pkgCrobtab)
        return content

    def _makeCrontabString(self, installRoot, pkgName, content):
        crontabString = ''
        if not installRoot or not pkgName:
            return crontabString

        crontabString += self._begin
        crontabString += self._installRootPrefix + installRoot + '\n'
        crontabString += self._packagePrefix + pkgName + '\n'
        crontabString += content
        crontabString += self._end
        return crontabString
