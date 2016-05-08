#! /usr/bin/python

import re
import file_util

class RootState:
    def __init__(self, time, command, installRoot,
                 version, activePkgs, pkgSettings):
        self.time = time
        self.command = command
        self.installRoot = installRoot
        self.version = version
        self.activePkgs = activePkgs
        self.pkgSettings = pkgSettings

class RootStateStreamer:
    def __init__(self):
        self._patternList = ['ainst.timestamp: ', 'ainst.command: ', 
                            'ainst.install_root: ', 'ainst.version: ']
        self._activePkgPrefix = 'ainst.active_package: '
        self._pkgSettingPrefix = 'ainst.settings: '

    def toString(self, rootState):
        content = ''
        try:
            content = '%s%d\n' % (self._patternList[0], rootState.time)
            content += '%s%s\n' % (self._patternList[1], rootState.command)
            content += '%s%s\n' % (self._patternList[2], rootState.installRoot)
            content += '%s%s\n' % (self._patternList[3], rootState.version)
            if rootState.activePkgs:
                for activePkg, activeTime in rootState.activePkgs:
                    content += '%s%s|%d\n' % (self._activePkgPrefix,
                                              activePkg, activeTime)
            if rootState.pkgSettings:
                for pkgName, keyValue in rootState.pkgSettings.iteritems():
                    content += '%s%s\n' % (self._pkgSettingPrefix, pkgName)
                    for key, value in keyValue.iteritems():
                        content += '%s %s\n' % (key, value)
        except Exception, e:
            return None
        return content

    def getRootStateFromFile(self, filePath):
        content = file_util.readFromFile(filePath)
        if not content:
            return None
        return self.toRootState(content)

    def toRootState(self, content):
        if not content:
            return None
        lines = content.split('\n')
        valueList = []
        activePkgs = []
        pkgSettings = {}
        currentPkg = None
        inSettings = False
        for index in range(len(lines)):
            line = lines[index]
            if line.strip() == '':
                continue
            if index == 0:
                match = re.match('%s(\d+)' % self._patternList[index], line)
                if not match:
                    return None
                valueList.append(float(match.group(1)))
            elif index < len(self._patternList):
                match = re.match('%s(.*)' % self._patternList[index], line)
                if not match:
                    return None
                valueList.append(match.group(1))
            elif not inSettings:
                if not self._parseActivePkg(line, activePkgs):
                    ret, pkg = self._parsePkgSettings(line, pkgSettings)
                    if not ret:
                        return None
                    inSettings = True
                    currentPkg = pkg
            else:
                ret, pkg = self._parsePkgSettings(line, pkgSettings)
                if not ret:
                    if not self._parseKeyValue(line, pkgSettings[currentPkg]):
                        return None
                else:
                    currentPkg = pkg
            index += 1
        return RootState(valueList[0], valueList[1], valueList[2],
                         valueList[3], activePkgs, pkgSettings)

    def _parseActivePkg(self, line, activePkgs):
        match = re.match('%s(.*)\|(\d+)' % self._activePkgPrefix, line)
        if match:
            activePkgs.append((match.group(1), int(match.group(2))))
            return True
        return False

    def _parsePkgSettings(self, line, pkgSettings):
        match = re.match('%s(\S+)' % self._pkgSettingPrefix, line)
        if match:
            currentPkg = match.group(1)
            pkgSettings[currentPkg] = {}
            return True, currentPkg
        return False, None

    def _parseKeyValue(self, line, keyValue):
        match = re.match('(\S+) (\S+)', line)
        if match:
            keyValue[match.group(1)] = match.group(2)
            return True
        return False
        


if __name__ == '__main__':
    filePath = '/home/xiaoming.zhang/xx/var/ainst/save/root-state-0'
    state = RootStateStreamer().getRootStateFromFile(filePath)
    print state.time
    print state.command
    print state.installRoot
    print state.version
    print state.activePkgs
    print state.pkgSettings
