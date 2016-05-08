#! /usr/bin/python

import file_util

class RemoteParam:
    def __init__(self, options=None):
        self.host = None
        self.hostFile = []
        self.remoteUser = None
        self.remoteSudo = False
        self.remoteTimeout = 1200
        self.errorContinue = False
        self.retryTime = 0
        self.retryInterval = 0
        self.parallel = 1
        self.removeDeactive = False
        self.remoteBin = ''
        self.remoteConf = ''
        RemoteParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'host'):
            self.host = options.host
        if hasattr(options, 'hostFile'):
            self.hostFile = options.hostFile
        if hasattr(options, 'remoteUser'):
            self.remoteUser = options.remoteUser
        if hasattr(options, 'remoteSudo'):
            self.remoteSudo = options.remoteSudo
        if hasattr(options, 'remoteTimeout'):
            self.remoteTimeout = options.remoteTimeout
        if hasattr(options, 'errorContinue'):
            self.errorContinue = options.errorContinue
        if hasattr(options, 'retryTime'):
            self.retryTime = options.retryTime
        if hasattr(options, 'retryInterval'):
            self.retryInterval = options.retryInterval
        if hasattr(options, 'parallel'):
            self.parallel = options.parallel
        if hasattr(options, 'removeDeactive'):
            self.removeDeactive = options.removeDeactive
        if hasattr(options, 'remoteBin'):
            self.remoteBin = options.remoteBin
        if hasattr(options, 'remoteConf'):
            self.remoteConf = options.remoteConf

class ActionParam(RemoteParam):
    def __init__(self, options=None):
        RemoteParam.__init__(self, options)
        self.dryRun = False
        ActionParam._init(self, options)

    def _init(self, options):
        if options and hasattr(options, 'dryRun'):
            self.dryRun = options.dryRun

class SetParam(RemoteParam):
    def __init__(self, options=None, settings=[]):
        RemoteParam.__init__(self, options)
        self.settings = settings
        self.setFiles = []
        SetParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'setFiles'):
            for setFile in options.setFiles:
                self.setFiles.append(file_util.getAbsPath(setFile))

class UnsetParam(RemoteParam):
    def __init__(self, options=None, unsetKeys=[]):
        RemoteParam.__init__(self, options)
        self.unsetKeys = unsetKeys
        self.unsetFiles = []
        UnsetParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'unsetFiles'):
            for unsetFile in options.unsetFiles:
                self.unsetFiles.append(file_util.getAbsPath(unsetFile))

class SaveParam(RemoteParam):
    def __init__(self, options=None):
        RemoteParam.__init__(self, options)
        self.file = None
        SaveParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'file'):
            self.file = options.file

class RestoreParam(RemoteParam):
    def __init__(self, options=None):
        RemoteParam.__init__(self, options)
        self.dryRun = False
        self.previous = False
        self.stateNumber = None
        self.stateFile = None
        self.timeStr = None
        self.noStart = False
        self.noExecute = False
        self.noStop = False
        self.repos = []
        self.confirmYes = False
        RestoreParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'previous'):
            self.previous = options.previous
        if hasattr(options, 'stateNumber'):
            self.stateNumber = options.stateNumber
        if hasattr(options, 'stateFile'):
            self.stateFile = options.stateFile
        if hasattr(options, 'timeStr'):
            self.timeStr = options.timeStr
        if hasattr(options, 'noStart'):
            self.noStart = options.noStart
        if hasattr(options, 'noStop'):
            self.noStop = options.noStop
        if hasattr(options, 'noExecute'):
            self.noExecute = options.noExecute
        if hasattr(options, 'repos'):
            self.repos = options.repos
        if hasattr(options, 'dryRun'):
            self.dryRun = options.dryRun
        if hasattr(options, 'confirmYes'):
            self.confirmYes = options.confirmYes

class HistoryParam(RemoteParam):
    def __init__(self, options=None):
        RemoteParam.__init__(self, options)
        self.count = None
        self.timeStr = None
        HistoryParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'count'):
            self.count = options.count
        if hasattr(options, 'timeStr'):
            self.timeStr = options.timeStr

class CrontabParam(RemoteParam):
    def __init__(self, options=None):
        RemoteParam.__init__(self, options)
        self.crontabOn = False
        self.crontabOff = False
        self.crontabList = False
        self.crontabUser = None
        CrontabParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'crontabOn'):
            self.crontabOn = options.crontabOn
        if hasattr(options, 'crontabOff'):
            self.crontabOff = options.crontabOff
        if hasattr(options, 'crontabList'):
            self.crontabList = options.crontabList
        if hasattr(options, 'crontabUser'):
            self.crontabUser = options.crontabUser
    
class ListParam(RemoteParam):
    def __init__(self, options=None):
        RemoteParam.__init__(self, options)
        self.repos = []
        self.repo = False
        self.allRoot = False
        self.requires = False
        self.provides = False
        self.conflicts = False
        self.obsoletes = False
        self.files = False
        self.configFiles = False
        self.settings = False
        self.scripts = False
        self.crontabs = False
        ListParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'repo'):
            self.repo = options.repo
        if hasattr(options, 'repos'):
            self.repos = options.repos
        if hasattr(options, 'allRoot'):
            self.allRoot = options.allRoot
        if hasattr(options, 'requires'):
            self.requires = options.requires
        if hasattr(options, 'provides'):
            self.provides = options.provides
        if hasattr(options, 'conflicts'):
            self.conflicts = options.conflicts
        if hasattr(options, 'obsoletes'):
            self.obsoletes = options.obsoletes
        if hasattr(options, 'files'):
            self.files = options.files
        if hasattr(options, 'configFiles'):
            self.configFiles = options.configFiles
        if hasattr(options, 'settings'):
            self.settings = options.settings
        if hasattr(options, 'scripts'):
            self.scripts = options.scripts
        if hasattr(options, 'crontabs'):
            self.crontabs = options.crontabs

class CacheParam(RemoteParam):
    def __init__(self, options):
        RemoteParam.__init__(self, options)
        self.repos = []
        CacheParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'repos'):
            self.repos = options.repos

class InstallBaseParam(RemoteParam):
    def __init__(self, options):
        RemoteParam.__init__(self, options)
        self.dryRun = False
        self.repos = []
        self.localRepos = []
        self.settings = []
        self.setFiles = []
        self.noStart = False
        self.noExecute = False
        self.check = False
        self.downgrade = False
        self.noUpgrade = False
        self.noExclusive = False
        self.confirmYes = False
        self.prefixFilter = ''
        InstallBaseParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'repos'):
            self.repos = options.repos
        if hasattr(options, 'localRepos'):
            for repo in options.localRepos:
                self.localRepos.append(file_util.getAbsPath(repo))
        if hasattr(options, 'settings'):
            self.settings = options.settings
        if hasattr(options, 'setFiles'):
            for setFile in options.setFiles:
                self.setFiles.append(file_util.getAbsPath(setFile))
        if hasattr(options, 'noStart'):
            self.noStart = options.noStart
        if hasattr(options, 'noExecute'):
            self.noExecute = options.noExecute
        if hasattr(options, 'check'):
            self.check = options.check
        if hasattr(options, 'downgrade'):
            self.downgrade = options.downgrade
        if hasattr(options, 'noUpgrade'):
            self.noUpgrade = options.noUpgrade
        if hasattr(options, 'noExclusive'):
            self.noExclusive = options.noExclusive
        if hasattr(options, 'dryRun'):
            self.dryRun = options.dryRun
        if hasattr(options, 'confirmYes'):
            self.confirmYes = options.confirmYes
        if hasattr(options, 'remoteRepos'):
            self.remoteRepos = options.remoteRepos
        if hasattr(options, 'prefixFilter'):
            self.prefixFilter = options.prefixFilter

class InstallParam(InstallBaseParam):
    def __init__(self, options):
        InstallBaseParam.__init__(self, options)
        self.noActivate = False
        InstallParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'noActivate'):
            self.noActivate = options.noActivate

class ActivateParam(InstallBaseParam):
    def __init__(self, options):
        InstallBaseParam.__init__(self, options)

class RemoveBaseParam(RemoteParam):
    def __init__(self, options):
        RemoteParam.__init__(self, options)
        self.dryRun = False
        self.noExecute = False
        self.noStop = False
        self.noDependents = False
        self.confirmYes = False
        RemoveBaseParam._init(self, options)

    def _init(self, options):
        if not options:
            return True
        if hasattr(options, 'noExecute'):
            self.noExecute = options.noExecute
        if hasattr(options, 'noStop'):
            self.noStop = options.noStop
        if hasattr(options, 'noDependents'):
            self.noDependents = options.noDependents
        if hasattr(options, 'dryRun'):
            self.dryRun = options.dryRun
        if hasattr(options, 'confirmYes'):
            self.confirmYes = options.confirmYes

class RemoveParam(RemoveBaseParam):
    def __init__(self, options):
        RemoveBaseParam.__init__(self, options)

class DeactivateParam(RemoveBaseParam):
    def __init__(self, options):
        RemoveBaseParam.__init__(self, options)

if __name__ == '__main__':
    import sys
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('', '--disableRepos', dest='disableRepos',default=False)
    options, args = parser.parse_args(sys.argv[1:])
    print options
    param = InstallParam(options)
    print param.disableRepos
