#! /usr/bin/python

import os
import ConfigParser
import time_util
from ainst_config import AinstConfig, RepoConfigItem
import arch
import rpm
import file_util

class _AinstConfigReplacer:
    def replaceBaseUrl(self, ainstConf):
        ainstConf.basearch = arch.getBaseArch()
        ainstConf.arch = arch.getCanonArch()
        ainstConf.releasever = self._getReleaseVer(ainstConf.distroverpkg)
        for name, item in ainstConf.repoConfigItems.items():
            del ainstConf.repoConfigItems[name]
            name = name.replace('$releasever', ainstConf.releasever)
            name = name.replace('$basearch', ainstConf.basearch)
            item.baseurl = self._replaceRepoBaseUrl(item.baseurl,
                                                    ainstConf.releasever,
                                                    ainstConf.basearch)
            ainstConf.repoConfigItems[name] = item

    def _replaceRepoBaseUrl(self, baseurl, releasever, basearch):
        baseurl = baseurl.replace('$releasever', releasever)
        baseurl = baseurl.replace('$basearch', basearch)
        return baseurl

    def _getReleaseVer(self, distroverpkg):
        '''Calculate the release version for the system.
        @param installroot: The value of the installroot option.
        @param distroverpkg: The value of the distroverpkg option.
        @return: The release version as a string (eg. '4' for FC4)
        '''
        ts = rpm.TransactionSet('/')
        ts.setVSFlags(~(rpm._RPMVSF_NOSIGNATURES|rpm._RPMVSF_NODIGESTS))
        idx = ts.dbMatch('provides', distroverpkg)
        # we're going to take the first one - if there is more than one of these
        # then the user needs a beating
        if idx.count() == 0:
            releasever = '$releasever'
        else:
            hdr = idx.next()
            releasever = hdr['version']
            del hdr
        del idx
        del ts
        return releasever

class AinstConfigParser:
    def parseFromFile(self, fileName):
        configParser = ConfigParser.ConfigParser()
        content = None
        try:
            content = configParser.read(fileName)
        except:
            return None
        sections = configParser.sections()
        if not content or not sections\
                or not configParser.has_section('main'):
            return None
        ainstConf = AinstConfig()
        try:
            for section in sections:
                if section == 'main':
                    self._parseMainSection(configParser.items(section), ainstConf)
                elif not self._parseRepoSection(section,
                                                configParser.items(section),
                                                ainstConf):

                    return None

            repoFileList = self._getRepoFileList(ainstConf.reposdir)
            for repoFile in repoFileList:
                if not self.parseRepoItemFromRepoFile(repoFile, ainstConf):
                    print "parse repo file failed."
                    return None
        except:
            return None
        self._replaceBaseUrl(ainstConf)
        return ainstConf

    def parseRepoItemFromRepoFile(self, fileName, ainstConf):
        configParser = ConfigParser.ConfigParser()
        content = configParser.read(fileName)
        sections = configParser.sections()
        if content is None or sections is None:
            return False
        for section in sections:
            if not self._parseRepoSection(section, configParser.items(section),
                                          ainstConf):
                return False
        return True

    def _parseMainSection(self, items, ainstConf):
        for key, value in items:
            if key == 'reposdir':
                repodirs = value.split(',')
                for repodir in repodirs:
                    repodir = repodir.strip()
                    ainstConf.reposdir.append(repodir)
            elif key == 'installonlypkgs':
                ainstConf.installonlypkgs = value
            elif key == 'exactarch':
                ainstConf.exactarch = int(value)
            elif key == 'timeout':
                ainstConf.timeout = float(value)
            elif key == 'installroot':
                ainstConf.installroot = file_util.getAbsPath(value)
            elif key == 'ainstroot':
                ainstConf.ainstroot = file_util.getAbsPath(value)
                ainstConf.rootinfo = ainstConf.ainstroot + '/root.info'
                ainstConf.cachedir = ainstConf.ainstroot + '/cache/'
            elif key == 'keepcache':
                ainstConf.keepcache = int(value)
            elif key == 'maxfilelength':
                ainstConf.maxfilelength = int(value)
            elif key == 'retrytime':
                ainstConf.retrytime = int(value)
            elif key == 'sockettimeout':
                ainstConf.sockettimeout = int(value)
            elif key == 'logfile':
                ainstConf.logfile = value
            elif key == 'loglevel':
                ainstConf.loglevel = value
            elif key == 'distroverpkg':
                ainstConf.distroverpkg = value
            elif key == 'expiretime':
                ainstConf.expiretime = time_util.stringToSecond(value)
            elif key == 'autostart':
                ainstConf.autostart = bool(value)

        return True

    def _parseRepoSection(self, section, items, ainstConf):
        if ainstConf.repoConfigItems.has_key(section):
            return False
        repoItem = RepoConfigItem()
        for key, value in items:
            if key == 'name':
                repoItem.name = value
            elif key == 'enabled':
                repoItem.enabled = int(value)
            elif key == 'baseurl':
                repoItem.baseurl = value
            elif key == 'mirrorlist':
                repoItem.mirrorlist = value
            elif key == 'gpgcheck':
                repoItem.gpgcheck = int(value)
        ainstConf.repoConfigItems[section] = repoItem
        return True

    def _getRepoFileList(self, reposdir):
        repoFileList = []
        for repodir in reposdir:
            if not file_util.exists(repodir):
                continue
            files = file_util.listDir(repodir)
            if files:
                for fileName in files:
                    if fileName.endswith('.repo'):
                        repoFileList.append(repodir + '/' + fileName)
        return repoFileList

    def _replaceBaseUrl(self, ainstConf):
        replacer = _AinstConfigReplacer()
        replacer.replaceBaseUrl(ainstConf)
        

if __name__ == '__main__':
    parser = AinstConfigParser()
    conf = parser.parseFromFile('./ainst2.conf')
    print conf
