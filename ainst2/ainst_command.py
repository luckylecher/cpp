#! /usr/bin/python

import os
import error
import common
import optparse
import rpmutils
import ainst_initer
import operator_builder
from remote_operator import RemoteOperator
from ainst_config_parser import AinstConfigParser
from ainst_config import RepoConfigItem
from operator_builder import InstallRootType
from ainst_operator import OperatorRet
from package_object import PackageObject
from operator_param import *

class AinstCommandBase(object):
    def __init__(self):
        self._names = []
        self._summary = None
        self._parser = optparse.OptionParser(usage=self._getUsage(),
                                             version='%prog ' + common.AINST_VERSION)
        self._command = None
        self._options = None
        self._args = None

    def getNames(self):
        return self._names

    def getSummary(self):
        return self._summary

    def _getUsage(self):
        return 'ainst2 cmd [option]\n\n' +\
            'see more: --help'

    def _addOption(self):
        self._parser.add_option('-i', '--installroot', dest='installRoot',
                                default=None, help='install root')
        self._parser.add_option('-c', dest='ainstConfFile',
                                default='/etc/ainst2.conf', help='ainst config file')
        self._parser.add_option('-v', '--verbose', dest='verbose', default=False,
                                action='store_true', help='print more info')
        self._addRemoteOptions()

    def _checkArgs(self):
        return True

    def _addReposOptions(self):
        self._parser.add_option('', '--disablerepo', dest='repos', type='string',
                                action='callback', callback=self._reposOptionCallback,
                                default=[], help='disable repos')
        self._parser.add_option('', '--enablerepo', dest='repos', type='string',
                                action='callback', callback=self._reposOptionCallback,
                                default=[], help='enable repos')

    def _reposOptionCallback(self, option, opt, value, parser):
        if opt == '--disablerepo':
            parser.values.repos.append({'disable':value})
        elif opt == '--enablerepo':
            parser.values.repos.append({'enable':value})

    def _addRemoteOptions(self):
        self._parser.add_option('', '--host', dest='host', default=None,
                                help='spefic remote host to execute')
        self._parser.add_option('', '--hostfile', dest='hostFile',
                                default=[], action='append',
                                help='spefic remote host to execute')
        self._parser.add_option('', '--remotetimeout', dest='remoteTimeout', type='int',
                                default=1200, help='time of remote execute, default 1200')
        self._parser.add_option('', '--continue', dest='errorContinue',
                                action='store_true', default=False,
                                help='continue process when one host error')
        self._parser.add_option('', '--retrytime', dest='retryTime', type='int',
                                default=0, help='time of retry when error')
        self._parser.add_option('', '--retryinterval', dest='retryInterval', type='int',
                                default=0, help='interval of between two retries')
        self._parser.add_option('', '--remoteuser', dest='remoteUser', default=None,
                                help='spefic remote user')
        self._parser.add_option('', '--remotesudo', dest='remoteSudo', default=False,
                                action='store_true', help='spefic whether sudo on remote host')
        self._parser.add_option('-p', '--parallel', dest='parallel', default=1,
                                type='int', help='max parallel process count, default 1')
        self._parser.add_option('', '--remotebin', dest='remoteBin', default=None,
                                help='spefic remote ainst2 bin full path')
        self._parser.add_option('', '--remoteconf', dest='remoteConf', default=None,
                                help='spefic remote ainst2 conf full path')

    def _setCommandStr(self, argv):
        self._command = self._names[0]
        for arg in argv:
            self._command += ' ' + arg

    def execute(self, argv):
        self._setCommandStr(argv)
        self._addOption()
        self._options, self._args = self._parser.parse_args(argv)
        if not self._checkArgs():
            return False
        ret = self._doExecute(self._args)
        return ret

class AinstInstallCommandBase(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._addReposOptions()
        self._parser.add_option('', '--localrepo', dest='localRepos',
                                action='append', default=[],
                                help='use local repos')
        self._parser.add_option('', '--remoterepo', dest='remoteRepos',
                                action='append', default=[],
                                help='use remote repos, the remote repos must be yum style repos')
        self._parser.add_option('', '--set', dest='settings',
                                action='append', default=[],
                                help='set settings for pkg')
        self._parser.add_option('', '--setfile', dest='setFiles',
                                action='append', default=[],
                                help='set setting from file')
        self._parser.add_option('', '--nostart', dest='noStart',
                                action='store_true', default=False,
                                help='suppress start the pkgs')
        self._parser.add_option('', '--noexecute', dest='noExecute',
                                action='store_true', default=False,
                                help='not execute scripts,such as pre-active')
        self._parser.add_option('', '--check', dest='check',
                                action='store_true', default=False,
                                help='check all of the prerequisites pkgs')
        self._parser.add_option('', '--downgrade', dest='downgrade',
                                action='store_true', default=False,
                                help='permit downgrade pkg version')
        self._parser.add_option('', '--noupgrade', dest='noUpgrade',
                                action='store_true', default=False,
                                help='prevent upgrade pkg version')
        self._parser.add_option('', '--noexclusive', dest='noExclusive',
                                action='store_true', default=False,
                                help='please cautiously use!!! premit require exclusive')
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')
        self._parser.add_option('-y', '--yes', dest='confirmYes',
                                action='store_true', default=False,
                                help='need not input yes when confirm')
        self._parser.add_option('', '--forceinst', dest='prefixFilter',
                                default='', help='rpm relocation prefix used ' +
                                'to filter root installed packages. only ' +
                                'valid when installroot is specified. default ' +
                                'is none.')
        self._parser.add_option('', '--removeDeactive', dest='removeDeactive',
                                action='store_true', default=False,
                                help='remove deactived packages if any.')

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) < 1:
            print 'Failed: Missing package name\n'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, argv):
        raise NotImplementedError()
    

class AinstInstallCommand(AinstInstallCommandBase):
    def __init__(self):
        AinstInstallCommandBase.__init__(self)
        self._names = ['install', 'inst']
        self._summary = 'Install a package or packages'

    def _addOption(self):
        AinstInstallCommandBase._addOption(self)
        self._parser.add_option('', '--noactivate', dest='noActivate',
                                action='store_true', default=False,
                                help='no activate')
        
    def _getUsage(self):
        return 'ainst2 install pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 install aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = InstallParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command,
                                                installRoot, True)

        if hasattr(param, 'remoteRepos'):
            ret = self._genRemoteReposConf(ainstConf, param.remoteRepos)
            if not ret:
                return False

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.install(pkgs, param, self._command) \
                != OperatorRet.OPERATE_SUCCESS:
            print 'Install failed'
            operator.unlock()
            return False
        print 'Install success'
        operator.unlock()
        return True
    
    def _genRemoteReposConf(self, ainstConf, remoteRepos):
        seno = 1
        for remoteRepoUrl in remoteRepos:
            repoConfItem = RepoConfigItem()
            repoConfItem.name = "ainst2.tmp.repo" + str(seno)
            if remoteRepoUrl.endswith("/"):
                remoteRepoUrl = remoteRepoUrl[:-1]
            repoConfItem.baseurl = remoteRepoUrl
            ainstConf.repoConfigItems[repoConfItem.name] = repoConfItem
            seno += 1
        return True

class AinstActivateCommand(AinstInstallCommandBase):
    def __init__(self):
        AinstInstallCommandBase.__init__(self)
        self._names = ['activate', 'active']
        self._summary = 'Activate a package or packages'

    def _getUsage(self):
        return 'ainst2 activate pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 activate aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = ActivateParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command,
                                                installRoot, True)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init Failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.activate(pkgs, param, self._command) \
                != OperatorRet.OPERATE_SUCCESS:
            print 'Activate failed'
            operator.unlock()
            return False
        print 'Activate success'
        operator.unlock()
        return True

class AinstStartCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['start']
        self._summary = 'Start a package or packages'

    def _getUsage(self):
        return 'ainst2 start pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 start aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) < 1:
            print 'Failed: Missing pkg name\n'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        param = ActionParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.ANY_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.start(pkgs, param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Start failed'
            operator.unlock()
            return False
        print 'Start success'
        operator.unlock()
        return True

class AinstStopCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['stop']
        self._summary = 'Stop a package or packages'

    def _getUsage(self):
        return 'ainst2 stop pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 stop aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'            

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) < 1:
            print 'Failed: Missing pkg name\n'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        param = ActionParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.ANY_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.stop(pkgs, param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Stop failed'
            operator.unlock()
            return False
        print 'Stop success'
        operator.unlock()
        return True

class AinstRestartCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['restart']
        self._summary = 'Restart a package or packages'

    def _getUsage(self):
        return 'ainst2 restart pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 restart aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) < 1:
            print 'Failed: Missing pkg name\n'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        param = ActionParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.ANY_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.restart(pkgs, param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Restart failed'
            operator.unlock()
            return False
        print 'Restart success'
        operator.unlock()
        return True

class AinstReloadCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['reload']
        self._summary = 'Reload a package or packages'

    def _getUsage(self):
        return 'ainst2 reload pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 reload aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) < 1:
            print 'Failed: Missing pkg name\n'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        param = ActionParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.ANY_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.reload(pkgs, param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Reload failed'
            operator.unlock()
            return False
        print 'Reload success'
        operator.unlock()
        return True

class AinstRemoveCommandBase(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--noexecute', dest='noExecute',
                                action='store_true', default=False,
                                help='no execute pre-deactive and post-deactive script')
        self._parser.add_option('', '--nostop', dest='noStop',
                                action='store_true', default=False,
                                help='no execute stop script')
        self._parser.add_option('', '--nodependents', dest='noDependents',
                                action='store_true', default=False,
                                help='not remove/deactive the dependent pkgs')
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')
        self._parser.add_option('', '--yes', dest='confirmYes',
                                action='store_true', default=False,
                                help='need not input yes when confirm')

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) < 1:
            print 'Failed: Missing pkg name\n'
            print self._parser.format_help()
            return False
        return True

class AinstDeactivateCommand(AinstRemoveCommandBase):
    def __init__(self):
        AinstRemoveCommandBase.__init__(self)
        self._names = ['deactivate', 'deactive']
        self._summary = 'Deactivate a package or packages'

    def _getUsage(self):
        return 'ainst2 deactivate pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 deactivate aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = DeactivateParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command,
                                                installRoot, True)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.deactivate(pkgs, param, self._command) != \
                OperatorRet.OPERATE_SUCCESS:
            print 'Deactivate failed'
            operator.unlock()
            return False
        print 'Deactivate success'
        operator.unlock()
        return True

class AinstRemoveCommand(AinstRemoveCommandBase):
    def __init__(self):
        AinstRemoveCommandBase.__init__(self)
        self._names = ['remove', 'rm']
        self._summary = 'Remove a package or packages'

    def _getUsage(self):
        return 'ainst2 remove pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 remove aggregator --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = RemoveParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command,
                                                installRoot, True)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.remove(pkgs, param, self._command) != \
                OperatorRet.OPERATE_SUCCESS:          
            print 'Remove packages failed'
            operator.unlock()
            return False
        print 'Remove success'
        operator.unlock()
        return True

class AinstSaveCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['save']
        self._summary = 'Save ainst2 root state'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--file', dest='file',
                                default=None, help='save root state to file')

    def _getUsage(self):
        return 'ainst2 save [option]\n\n' +\
            'example: ainst2 save --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 save --file=./filename --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = SaveParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.save(param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Save ainst2 root state failed'
            operator.unlock()
            return False
        print 'Save success'
        operator.unlock()
        return True

class AinstRestoreCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['restore']
        self._summary = 'Restore root to state'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._addReposOptions()
        self._parser.add_option('', '--previous', dest='previous',
                                action='store_true', default=False,
                                help='Restore root to previous state')
        self._parser.add_option('', '--statenumber', dest='stateNumber', type='int',
                                default=None, help='Restore root to this state number')
        self._parser.add_option('', '--statefile', dest='stateFile',
                                default=None, help='Restore root to this state file')
        self._parser.add_option('', '--since', dest='timeStr',
                                default=None, help='Restore root to this time')
        self._parser.add_option('', '--nostart', dest='noStart',
                                action='store_true', default=False,
                                help='suppress start the pkgs')
        self._parser.add_option('', '--noexecute', dest='noExecute',
                                action='store_true', default=False,
                                help='noexecute')
        self._parser.add_option('', '--dryrun', dest='dryRun',
                                action='store_true', default=False,
                                help='just output operation, but not do anything')
        self._parser.add_option('', '--yes', dest='confirmYes',
                                action='store_true', default=False,
                                help='need not input yes when confirm')

    def _getUsage(self):
        return 'ainst2 restore [option]\n\n' +\
            'example: ainst2 restore --previous --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 restore --statenumber=1 --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 restore --statefile=./filename --installroot=/home/admin/ainst_install\n' +\
            '''         ainst2 restore --since='2013-06-22 00:00:00' --installroot=/home/admin/ainst_install\n\n''' +\
            'see more: --help'
    def _checkArgs(self):
        optionList = [self._options.previous, self._options.stateNumber,
                      self._options.stateFile, self._options.timeStr]
        optionCount = 0
        for option in optionList:
            if option is not None and option is not False:
                optionCount += 1
        if optionCount != 1:
            print 'Failed: Need one restore option(previous, stateNumber,'\
                ' stateFile or stateNumber)'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = RestoreParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command,
                                                installRoot, True)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False

        if operator.restore(param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Restore root to state failed'
            operator.unlock()
            return False
        print 'Restore success'
        operator.unlock()
        return True

class AinstHistoryCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['history']
        self._summary = 'show history of user operation'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--count', dest='count', type='int',
                                default=None, help='show the last count of history')
        self._parser.add_option('', '--since', dest='timeStr',
                                default=None, help='show history since time, Y-m-d H:M:S"')

    def _getUsage(self):
        return 'ainst2 history [option]\n\n' +\
            'example: ainst2 history --count=20 --installroot=/home/admin/ainst_install\n' +\
            '''         ainst2 history --since='2013-06-22 00:00:00' --installroot=/home/admin/ainst_install\n\n''' +\
            'see more: --help'

    def _checkArgs(self):
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = HistoryParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.history(param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Show history failed'
            operator.unlock()
            return False
        print 'History success'
        operator.unlock()
        return True

class AinstListCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['list', 'ls']
        self._summary = 'list infos'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._addReposOptions()
        self._parser.add_option('', '--repo', dest='repo', default=False,
                                action='store_true', help='show repos')
        self._parser.add_option('', '--allroot', dest='allRoot', 
                                default=False, action='store_true', 
                                help='show all install root pkg info')
        self._parser.add_option('', '--requires', dest='requires', default=False,
                                action='store_true', help='show package requires')
        self._parser.add_option('', '--provides', dest='provides', default=False,
                                action='store_true', help='show package provides')
        self._parser.add_option('', '--conflicts', dest='conflicts', default=False,
                                action='store_true', help='show package conflicts')
        self._parser.add_option('', '--obsoletes', dest='obsoletes', default=False,
                                action='store_true', help='show package obsoletes')
        self._parser.add_option('', '--files', dest='files', default=False,
                                action='store_true', help='show package files')        
        self._parser.add_option('', '--configfiles', dest='configFiles', default=False,
                                action='store_true', help='show package config files')
        self._parser.add_option('', '--settings', dest='settings', default=False,
                                action='store_true', help='show package settings')
        self._parser.add_option('', '--scripts', dest='scripts', default=False,
                                action='store_true', help='show package scripts')
        self._parser.add_option('', '--crontabs', dest='crontabs', default=False,
                                action='store_true', help='show package crontabs')

    def _getUsage(self):
        return 'ainst2 list [option]\n\n' +\
            'example: ainst2 list aggregator --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 list --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 list aggregator --installroot=/home/admin/ainst_install --requires --provides\n' +\
            '         ainst2 list aggregator --repo --installroot=/home/admin/ainst_install --scripts\n' +\
            '         ainst2 list aggregator --allroot --repo\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        if len(self._args) > 1:
            print 'Too many params for list command'
            print self._parser.format_help()
            return False
        return True

    def _doExecute(self, argv):
        if len(argv) > 1:
            print 'Too many params for list command'
            return False
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        param = ListParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.ANY_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.list(argv, param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'List failed'
            operator.unlock()
            return False
        print 'List success'
        operator.unlock()
        return True

class AinstCrontabCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['crontab']
        self._summary = 'crontab the pkgs'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--on', dest='crontabOn', default=False,
                                action='store_true', help='turn crontab of pkg on')
        self._parser.add_option('', '--off', dest='crontabOff', 
                                default=False, action='store_true', 
                                help='turn the crontab of pkg off')
        self._parser.add_option('', '--list', dest='crontabList', default=False,
                                action='store_true', help='show package crontab')
        self._parser.add_option('', '--user', dest='crontabUser', default=None,
                                help='spefic user to crontab command')

    def _getUsage(self):
        return 'ainst2 crontab pkg1 pkg2 ... [option]\n\n' +\
            'example: ainst2 crontab aggregator --list --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 crontab --list --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 crontab aggregator --on --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 crontab aggregator --off --installroot=/home/admin/ainst_install\n' +\
            '         ainst2 crontab aggregator --list --user=admin --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        if not self._checkOptions():
            print self._parser.format_help()
            return False
        return True

    def _checkOptions(self):
        optionCount = 0
        if self._options.crontabOn:
            optionCount += 1
        if self._options.crontabOff:
            optionCount += 1
        if self._options.crontabList:
            optionCount += 1
        if optionCount != 1:
            return False
        if not self._options.crontabList and len(self._args) < 1:
            return False
        return True

    def _doExecute(self, pkgs):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = CrontabParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.crontab(pkgs, param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Crontab command failed'
            operator.unlock()
            return False
        print 'Crontab command success'
        operator.unlock()
        return True

class AinstMakeCacheCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['makecache']
        self._summary = 'make cache of repo data'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._addReposOptions()

    def _getUsage(self):
        return 'ainst2 makecache [option]\n\n' +\
            'example: ainst2 makecache\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        param = CacheParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command)

        operator = operator_builder.getAinstOperator(ainstConf, None,
                                                     InstallRootType.NO_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.makeCache(param) != OperatorRet.OPERATE_SUCCESS:
            print 'Make cache failed'
            operator.unlock()
            return False
        print 'Make cache success'
        operator.unlock()
        return True

class AinstClearCacheCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['clearcache']
        self._summary = 'clear cache of repo data'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '-a', dest='clearAll', default=False,
                                action='store_true', help='clear all cache')
        self._addReposOptions()

    def _getUsage(self):
        return 'ainst2 clearcache [option]\n\n' +\
            'example: ainst2 clearcache\n' +\
            '         ainst2 clearcache -a\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        param = CacheParam(self._options)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command)

        operator = operator_builder.getAinstOperator(ainstConf, None,
                                                     InstallRootType.NO_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.clearCache(self._options) != OperatorRet.OPERATE_SUCCESS:
            print 'Clear cache failed'
            operator.unlock()
            return False
        print 'Clear cache success'
        operator.unlock()
        return True

class AinstSetCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['set']
        self._summary = 'set variables'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--setfile', dest='setFiles',
                                action='append', default=[],
                                help='set setting from file')

    def _getUsage(self):
        return 'ainst2 set pkgname.key=value [option]\n\n' +\
            'example: ainst2 set aggregator.port=9092 filter.port=22233 --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) == 0 and not self._options.setFiles:
            print 'Need set value or --setfile'
            print self._parser.format_help()
            return False
        for elem in self._args:
            items = elem.split('=')
            if len(items) < 2:
                print 'Set value need separator ='
                print self._parser.format_help()
                return False
            key = items[0]
            if len(key.split('.')) < 2:
                print 'Set key need separator . between pkg and key'
                print self._parser.format_help()
                return False
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = SetParam(self._options, self._args)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.set(param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Set settings failed'
            operator.unlock()
            return False
        print 'Set success'
        operator.unlock()
        return True

class AinstUnsetCommand(AinstCommandBase):
    def __init__(self):
        AinstCommandBase.__init__(self)
        self._names = ['unset']
        self._summary = 'unset variables'

    def _addOption(self):
        AinstCommandBase._addOption(self)
        self._parser.add_option('', '--unsetfile', dest='unsetFiles',
                                action='append', default=[],
                                help='unset setting from file')

    def _getUsage(self):
        return 'ainst2 unset pkgname.key [option]\n\n' +\
            'example: ainst2 unset aggregator.port filter.port --installroot=/home/admin/ainst_install\n\n' +\
            'see more: --help'

    def _checkArgs(self):
        if not AinstCommandBase._checkArgs(self):
            return False
        if len(self._args) == 0 and not self._options.unsetFiles:
            print 'Need unset value or --unsetfile'
            print self._parser.format_help()
            return False
        for elem in self._args:
            if len(elem.split('.')) < 2:
                print 'Unset key need separator . between pkg and key'
                print self._parser.format_help()
                return False
        return True

    def _doExecute(self, argv):
        ainstConf = AinstConfigParser().parseFromFile(self._options.ainstConfFile)
        if not ainstConf:
            print 'Parse ainst config[%s] failed' % self._options.ainstConfFile
            return False
        if not ainst_initer.initLogging(ainstConf, self._options.verbose):
            print 'Init logging failed'
            return False
        installRoot = ainst_initer.getInstallRoot(self._options.installRoot,
                                                  ainstConf)
        if not installRoot:
            print 'Install root is invalid'
            return False
        param = UnsetParam(self._options, self._args)
        if param.host or param.hostFile:
            remoteOperator = RemoteOperator()
            return remoteOperator.remoteOperate(param, self._command, installRoot)

        operator = operator_builder.getAinstOperator(ainstConf, installRoot,
                                                     InstallRootType.MUST_INSTALLROOT)
        if not operator:
            print 'Init failed'
            return False
        if not operator.lock():
            print 'Lock ainst2 failed: others is using ainst2'
            return False
        if operator.unset(param, self._command) != OperatorRet.OPERATE_SUCCESS:
            print 'Unset settings failed'
            operator.unlock()
            return False
        print 'Unset success'
        operator.unlock()
        return True


if __name__ == '__main__':
    a = '''
    argv = ['install', 'anet',
            '--installroot=/home/admin',
            '--disablerepo=extras']

    cmd = None
    if argv[0] in ['install', 'inst']:
        cmd = AinstInstallCommand()
    print cmd.execute(argv[1:])
'''
    import sys
    cmd = AinstSetCommand()
    print cmd.execute(sys.argv[1:])
    
