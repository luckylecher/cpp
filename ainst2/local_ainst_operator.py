#! /usr/bin/python

import error
import time
import time_util
import resolver
from logger import Log
from ainst_operator import AinstOperator, OperatorRet
from crontab_wrapper import CrontabWrapper
from crontab_info import CrontabInfoStreamer
from root_info import RootInfoDbStreamer
from package_util import PackageUtil
from root_state import RootStateStreamer
from setting_file_parser import SettingFileParser
from unset_file_parser import UnsetFileParser
from ainst_context import AinstContextBuilder
from resolver import RecursiveDepResolver, ResolverOption
from ainst_root import AinstRootReader, AinstRoot
from root_executor import CompositeExecutor
from root_install_executor import RootInstallExecutor
from root_activate_executor import RootActivateExecutor
from root_deactivate_executor import RootDeactivateExecutor
from root_remove_executor import RootRemoveExecutor
from root_save_executor import RootSaveExecutor
from root_set_executor import RootSetExecutor
from root_unset_executor import RootUnsetExecutor
from root_action_executor import RootStartExecutor, RootStopExecutor
from root_action_executor import RootRestartExecutor, RootReloadExecutor

class LocalAinstOperator(AinstOperator):
    def __init__(self, ainstConf, installRoot, ainstRoot):
        AinstOperator.__init__(self, ainstConf)
        self._installRoot = installRoot
        self._ainstRoot = ainstRoot
        self._contextBuilder = AinstContextBuilder()
        self._actionDict = {'start' : 'RootStartExecutor',
                            'stop' : 'RootStopExecutor',
                            'restart' : 'RootRestartExecutor',
                            'reload' : 'RootReloadExecutor'}

    def set(self, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, 'Set to invalid ainst root')
            return OperatorRet.OPERATE_FAILED

        pkgSettings = self._getPkgSettings(param.settings, param.setFiles)
        if not pkgSettings:
            Log.cout(Log.INFO, 'No settings to set')
            return OperatorRet.OPERATE_SUCCESS

        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         useRepo=False)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        activePkgs = self._selectInstalledPkgs(context, pkgSettings.keys())
        if not activePkgs:
            Log.cout(Log.ERROR, 'No active package to set settings')
            return OperatorRet.OPERATE_FAILED

        compositeExecutor = CompositeExecutor()
        self._getSetExecutor(compositeExecutor, pkgSettings, activePkgs)
        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Set settings failed')
            return OperatorRet.OPERATE_FAILED
        if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
            return OperatorRet.OPERATE_FAILED

        return OperatorRet.OPERATE_SUCCESS

    def unset(self, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, 'Unset to invalid ainst root')
            return OperatorRet.OPERATE_FAILED

        unsetKeys = self._getUnsetKeys(param.unsetKeys, param.unsetFiles)
        if not unsetKeys:
            Log.cout(Log.INFO, 'No unset key to unset')
            return OperatorRet.OPERATE_SUCCESS

        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         useRepo=False)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        activePkgs = self._selectInstalledPkgs(context, unsetKeys.keys())
        if not activePkgs:
            Log.cout(Log.ERROR, 'No active package to unset settings')
            return OperatorRet.OPERATE_FAILED

        compositeExecutor = CompositeExecutor()
        self._getUnsetExecutor(compositeExecutor, unsetKeys, activePkgs)
        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Unset settings failed')
            return OperatorRet.OPERATE_FAILED
        if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
            return OperatorRet.OPERATE_FAILED

        return OperatorRet.OPERATE_SUCCESS

    def list(self, pkgs, param, command):
        if len(pkgs) > 1:
            return OperatorRet.OPERATE_FAILED
        installRoots = []
        if param.allRoot or not self._installRoot:
            streamer = RootInfoDbStreamer()
            rootInfo = streamer.load(self._ainstConf.rootinfo)
            if rootInfo is None:
                Log.cout(Log.ERROR, 'Load root info failed')
                return OperatorRet.OPERATE_FAILED
            for root in rootInfo.installRootSet:
                installRoots.append(root)
            installRoots.append('/')
        else:
            installRoots.append(self._installRoot)

        context = self._contextBuilder.buildMultiRootContext(installRoots,
                                                             self._ainstConf,
                                                             param.repo,
                                                             param.repos)

        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        repo2Pkgs = None
        if len(pkgs) > 0:
            repo2Pkgs = context.searchPkgs(pkgs[0])
        else:
            repo2Pkgs = context.getPkgs()

        if repo2Pkgs is None or len(repo2Pkgs) == 0:
            Log.cout(Log.INFO, 'No available package found')
            return OperatorRet.OPERATE_SUCCESS

        indents = 2
        items = sorted(repo2Pkgs.items(), key=lambda item:item[0])
        for repo, pkgs in items:
            if len(pkgs) == 0:
                continue
            Log.cout(Log.INFO, "InstallRoot: %s" % repo)
            pkgs.sort(cmp=lambda x,y: cmp(str(x), str(y)))
            for pkg in pkgs:
                key = " " * indents + "Package: %s" % pkg
                value = 'Source: %s' % repo 
                Log.coutValue(Log.INFO, key, value)
                self._printPkgInfo(pkg, param, indents * 2)
                self._printPkgAicfInfo(pkg, param, indents * 2)
                self._printPkgFiles(pkg, param, indents * 2)
            Log.cout(Log.INFO, '')
        return OperatorRet.OPERATE_SUCCESS
        
    def _printPkgAicfInfo(self, pkg, param, indents):
        if not pkg or not hasattr(pkg, 'aicfInfo') or not pkg.aicfInfo:
            return 
        if param.configFiles:
            Log.cout(Log.INFO, " " * indents + "Config files: ")
            for configFile in pkg.aicfInfo.configs.keys():
                Log.cout(Log.INFO, " " * indents * 2 + configFile)
        if param.settings:
            reader = AinstRootReader(AinstRoot(pkg.repo.id))
            pkgSettings = reader.getPkgSettings(pkg.name)
            Log.cout(Log.INFO, " " * indents + "Settings: ")
            if pkgSettings.has_key(pkg.name):
                for key, value in pkgSettings[pkg.name].items():
                    Log.cout(Log.INFO, " " * indents * 2 + key + " : " + value)
        if param.scripts:
            Log.cout(Log.INFO, " " * indents + "Scripts: ")
            for key, value in pkg.aicfInfo.scripts.items():
                Log.cout(Log.INFO, " " * indents * 2 + key + " : " + value)
        if param.crontabs:
            Log.cout(Log.INFO, " " * indents + "Crontabs: ")
            for crontab in pkg.aicfInfo.crontabs:
                Log.cout(Log.INFO, " " * indents * 2 + crontab)

    def _printPkgFiles(self, pkg, param, indents):
        if not param.files:
            return
        Log.cout(Log.INFO, " " * indents + "Files: ")
        ainstRoot = AinstRoot(pkg.repo.id)
        reader = AinstRootReader(ainstRoot)
        fileList = reader.getActivePkgFiles(pkg)
        if fileList is None:
            if not hasattr(pkg, 'files'):
                return
            for fileName in pkg.files:
                Log.cout(Log.INFO, " " * indents * 2 + "%s" % fileName)
            return
        prefix = ainstRoot.getRoot()
        if prefix[-1] != '/':
            prefix += '/'
        fileList.sort()
        for fileName in fileList:
            Log.cout(Log.INFO, " " * indents * 2 + prefix + fileName)

    def history(self, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return OperatorRet.OPERATE_FAILED
        reader = AinstRootReader(self._ainstRoot)
        stateList = []
        if param.count and param.timeStr:
            Log.cout(Log.ERROR, 'Only one pattern indicated')
            return OperatorRet.OPERATE_FAILED

        elif param.timeStr:
            timeStamp = time_util.timeStr2Stamp(param.timeStr)
            if timeStamp is None:
                Log.cout(Log.ERROR, 'Time format illegal')
                return OperatorRet.OPERATE_FAILED
            stateList = reader.getLatestRootStateByTime(timeStamp)
        else:
            count = 10
            if param.count is not None:
                count = param.count
            stateList = reader.getLatestRootStateByCount(param.count)
            
        for number, state in stateList:
            timeStr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state.time))
            Log.cout(Log.INFO, "StateNumber:[%d] Time:[%s] Command:[%s]" %\
                         (number, timeStr, state.command))
        if not stateList:
            Log.cout(Log.INFO, 'No Command\n')
        return OperatorRet.OPERATE_SUCCESS
            
    def _addInstallRootToRootInfo(self):
        streamer = RootInfoDbStreamer()
        rootInfo = streamer.load(self._ainstConf.rootinfo)
        if rootInfo is None:
            Log.cout(Log.ERROR, 'Load root info failed')
            return False
        if self._installRoot not in rootInfo.installRootSet:
            rootInfo.installRootSet.add(self._installRoot)
            if not streamer.dump(rootInfo, self._ainstConf.rootinfo):
                Log.cout(Log.ERROR, 'Dump root info failed')
                return False
        return True

    def _removeInstallRootFromRootInfo(self):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return False
        reader = AinstRootReader(self._ainstRoot)
        if reader.isEffective():
            return True
        Log.cout(Log.INFO, 'Remove install root %s from root info..' %
                 self._installRoot)
        streamer = RootInfoDbStreamer()
        rootInfo = streamer.load(self._ainstConf.rootinfo)
        if rootInfo is None:
            Log.cout(Log.ERROR, 'Load root info failed')
            return False
        if self._installRoot in rootInfo.installRootSet:
            rootInfo.installRootSet.remove(self._installRoot)
            if not streamer.dump(rootInfo, self._ainstConf.rootinfo):
                Log.cout(Log.ERROR, 'Dump root info failed')
                return False
        return True

    def install(self, pkgs, param, command):
        if not self._ainstRoot.isAvailableAinstRoot():
            Log.cout(Log.ERROR, 'Install to unavailable ainst root')
            return OperatorRet.OPERATE_FAILED
        return self._doInstall(pkgs, param, command, True)

    def activate(self, pkgs, param, command):
        if not self._ainstRoot.isAvailableAinstRoot():
            Log.cout(Log.ERROR, 'Activate to unavailable ainst root')
            return OperatorRet.OPERATE_FAILED
        return self._doInstall(pkgs, param, command, False)

    def _doInstall(self, pkgs, param, command, isInstallCommand):
        if not pkgs:
            return OperatorRet.OPERATE_FAILED
        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         True,
                                                         param.repos,
                                                         param.localRepos)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        context.setPrefixFilter(param.prefixFilter)
        
        installPkgs = self._selectInstallPkgs(context, pkgs)
        if not installPkgs:
            Log.cout(Log.INFO, 'No package to install')
            return OperatorRet.OPERATE_FAILED

        resolverOption = ResolverOption()
        if param.check:
            resolverOption.checkType = ResolverOption.CHECK_INSTALLED
        if param.downgrade:
            resolverOption.downgrade = True
        if param.noUpgrade:
            resolverOption.upgrade = False
        if param.noExclusive:
            resolverOption.exclusiveDeps = False
        if isInstallCommand and param.noActivate:
                resolverOption.sameProvideCoexits = True

        depResolver = RecursiveDepResolver(context, resolverOption)
        ret, operations, topOrder = depResolver.install(installPkgs)
        if ret != error.ERROR_NONE:
            Log.cout(Log.ERROR, 'Dependency resovle failed')
            return OperatorRet.OPERATE_FAILED

        reader = AinstRootReader(self._ainstRoot)
        installedPkgs = reader.getInstallPackages()

        if isInstallCommand and param.noActivate:
            return self._doInstallExecute(param, operations, topOrder, installedPkgs)
        return self._doActivateExecute(param, operations, topOrder,
                                       installedPkgs, command)

    def _doInstallExecute(self, param, operations, topOrder, installedPkgs):
        keyValueList = []
        compositeExecutor = CompositeExecutor()
        self._getInstallExecutor(compositeExecutor, operations, topOrder,
                                 param, installedPkgs, keyValueList)
        if not keyValueList:
            Log.cout(Log.INFO, 'No effective operations')
            return OperatorRet.OPERATE_SUCCESS                
        Log.coutValueList(Log.INFO, keyValueList)
        if not param.dryRun:
            if not param.confirmYes and not Log.coutConfirm():
                return OperatorRet.OPERATE_SUCCESS
        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Install packages failed')
            return OperatorRet.OPERATE_FAILED
        if not param.dryRun:
            if compositeExecutor.isExecuted():
                if not self._addInstallRootToRootInfo():
                    Log.cout(Log.ERROR, 'Add install root to root info failed')
                    compositeExecutor.undo()
                    return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def _getInstallExecutor(self, compositeExecutor, operations,
                            topOrder, param, installedPkgs, keyValueList):
        if not operations or not topOrder:
            return True
        for pkg in topOrder:
            if operations.has_key(pkg) and operations[pkg] == resolver.INSTALL\
                    and PackageUtil.getPkgNameVersion(pkg) not in installedPkgs:
                keyValueList.append(('%s' % pkg, 'install'))
                executor = RootInstallExecutor(self._ainstRoot,
                                               self._ainstConf,
                                               pkg, 
                                               param.dryRun)
                compositeExecutor.appendExecutor(executor)
        return True

    def _doActivateExecute(self, param, operations, topOrder,
                           installedPkgs, command):
        keyValueList = []
        settings = self._getPkgSettings(param.settings, param.setFiles)
        compositeExecutor = CompositeExecutor()
        needAction = self._getActivateExecutor(compositeExecutor, operations, topOrder,
                                               param, installedPkgs, keyValueList, settings)
        if not needAction:
            Log.cout(Log.INFO, 'No effective operations')
            return OperatorRet.OPERATE_SUCCESS
        Log.coutValueList(Log.INFO, keyValueList)
        if not param.dryRun:
            if not param.confirmYes and not Log.coutConfirm():
                return OperatorRet.OPERATE_SUCCESS
        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Active packages failed')
            return OperatorRet.OPERATE_FAILED
        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS

        if compositeExecutor.isExecuted():
            saveExecutor = RootSaveExecutor(self._ainstRoot, self._ainstConf, command)
            compositeExecutor.appendExecutor(saveExecutor)
            if not compositeExecutor.execute():
                Log.cout(Log.ERROR, 'Save root state failed')
                return OperatorRet.OPERATE_FAILED
            if not self._addInstallRootToRootInfo():
                Log.cout(Log.ERROR, 'Add install root to root info failed')
                compositeExecutor.undo()
                return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def _getSetExecutor(self, compositeExecutor, settings, activePkgs):
        if not activePkgs:
            return True
        for pkg in activePkgs:
            if pkg.name in settings:
                executor = RootSetExecutor(self._ainstRoot, self._ainstConf,
                                           pkg, settings[pkg.name])
                compositeExecutor.appendExecutor(executor)
        return True

    def _getUnsetExecutor(self, compositeExecutor, unsetKeys, activePkgs):
        if not activePkgs:
            return True
        for pkg in activePkgs:
            if pkg.name in unsetKeys:
                executor = RootUnsetExecutor(self._ainstRoot, self._ainstConf,
                                             pkg, unsetKeys[pkg.name])
                compositeExecutor.appendExecutor(executor)
        return True

    def _getUnsetKeys(self, unsetKeys, unsetFiles=[]):
        keyDict = {}
        parser = UnsetFileParser()
        if unsetFiles:
            for unsetFile in unsetFiles:
                keys = parser.parse(unsetFile)
                if keys is None:
                    Log.cout(Log.WARNING, 'Unset file %s parse failed' % unsetFile)
                    continue
                keyDict.update(keys)
                
        if not unsetKeys:
            return keyDict

        for keyItem in unsetKeys:
            items = keyItem.split('.')
            if len(items) < 2:
                continue
            pkgName = items[0]
            key = ('.').join(items[1:])
            keyDict.setdefault(pkgName, set([])).add(key)

        return keyDict

    def _getPkgSettings(self, settingList, setFiles=[]):
        pkgSettings = {}
        parser = SettingFileParser()
        if setFiles:
            for setFile in setFiles:
                settings = parser.parse(setFile)
                if settings is None:
                    Log.cout(Log.WARNING, 'Set file %s parse failed' % setFile)
                    continue
                pkgSettings.update(settings)

        if not settingList:
            return pkgSettings

        for kvPair in settingList:
            kv = kvPair.split('=')
            if len(kv) < 2:
                continue
            pkgNameAndSettingkey = kv[0]
            pkgSettingValue = kv[1]
            if len(kv) > 2:
                pkgSettingValue = ('=').join(kv[1:])
            items = pkgNameAndSettingkey.split('.')
            if len(items) < 2:
                continue
            pkgName = items[0]
            pkgSettingKey = items[1]
            if len(items) > 2:
                pkgSettingKey = ('.').join(items[1:])
            if not pkgSettings.has_key(pkgName):
                pkgSettings[pkgName] = dict()
            pkgSettings[pkgName][pkgSettingKey] = pkgSettingValue
        return pkgSettings

    def _getActivateExecutor(self, compositeExecutor, operations, topOrder,
                             param, installedPkgs, keyValueList, settings={},
                             unsetKeys={}):
        needAction = False
        for pkg in topOrder:
            pkgAddSettings = {}
            if settings.has_key(pkg.name):
                pkgAddSettings = settings[pkg.name]
            unsetKey = set()
            if unsetKeys.has_key(pkg.name):
                unsetKey = unsetKeys[pkg.name]
            if operations.has_key(pkg):
                if operations[pkg] == resolver.INSTALL:
                    needAction = True
                    if PackageUtil.getPkgNameVersion(pkg) not in installedPkgs:
                        keyValueList.append(('%s' % pkg, 'install'))
                        executor = RootInstallExecutor(self._ainstRoot, 
                                                       self._ainstConf,
                                                       pkg,
                                                       param.dryRun)
                        compositeExecutor.appendExecutor(executor)
                    keyValueList.append(('%s' % pkg, 'activate'))
                    executor = RootActivateExecutor(self._ainstRoot, 
                                                    self._ainstConf,
                                                    pkg,
                                                    param.noStart,
                                                    param.noExecute,
                                                    pkgAddSettings,
                                                    param.dryRun,
                                                    unsetKey)
                    compositeExecutor.appendExecutor(executor)
                elif operations[pkg] == resolver.REMOVE:
                    needAction = True
                    keyValueList.append(('%s' % pkg, 'deactivate'))
                    executor = RootDeactivateExecutor(self._ainstRoot,
                                                      self._ainstConf,
                                                      pkg,
                                                      param.noStart,
                                                      param.noExecute,
                                                      {},
                                                      param.dryRun)
                    compositeExecutor.appendExecutor(executor)
                    if param.removeDeactive:
                        keyValueList.append(('%s' % pkg, 'remove'))
                        executor = RootRemoveExecutor(self._ainstRoot,
                                                      self._ainstConf,
                                                      pkg,
                                                      param.dryRun)
                        compositeExecutor.appendExecutor(executor)
            elif pkgAddSettings:
                needAction = True
                keyValueList.append(('%s' % pkg, 'set settings'))
                executor = RootSetExecutor(self._ainstRoot, 
                                           self._ainstConf,
                                           pkg,
                                           pkgAddSettings,
                                           param.dryRun)
                compositeExecutor.appendExecutor(executor)                
            elif unsetKey:
                needAction = True
                keyValueList.append(('%s' % pkg, 'unset settings'))
                executor = RootUnsetExecutor(self._ainstRoot, 
                                             self._ainstConf,
                                             pkg,
                                             unsetKey,
                                             param.dryRun)
                compositeExecutor.appendExecutor(executor)
        return needAction

    def deactivate(self, pkgs, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, 'Deactivate to invalid ainst root')
            return OperatorRet.OPERATE_FAILED

        if not pkgs:
            return OperatorRet.OPERATE_FAILED
        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         useRepo=False)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        removePkgs = self._selectInstalledPkgs(context, pkgs)
        if not removePkgs:
            Log.cout(Log.ERROR, 'No package to deactivate')
            return OperatorRet.OPERATE_FAILED

        if param.noDependents:
            return self._doDeactivateNoDependents(removePkgs, param, command)

        resolverOption = ResolverOption()
        depResolver = RecursiveDepResolver(context, resolverOption)
        ret, operations, topOrder = depResolver.remove(removePkgs)
        if ret != error.ERROR_NONE:
            Log.cout(Log.ERROR, 'Dependency resovle failed')
            return OperatorRet.OPERATE_FAILED

        keyValueList = []
        compositeExecutor = CompositeExecutor()
        self._doDeactivate(compositeExecutor, operations, topOrder,
                           param, keyValueList)
        if not keyValueList:
            Log.cout(Log.INFO, 'No effective operations')
            return OperatorRet.OPERATE_SUCCESS                

        Log.coutValueList(Log.INFO, keyValueList)
        if not param.dryRun:
            if not param.confirmYes and not Log.coutConfirm():
                return OperatorRet.OPERATE_SUCCESS

        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Deactive packages failed')
            return OperatorRet.OPERATE_FAILED
        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS

        if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS        

    def _doDeactivateNoDependents(self, removePkgs, param, command):
        compositeExecutor = CompositeExecutor()
        for pkg in removePkgs:
            Log.coutValue(Log.INFO, '%s' % pkg, 'deactivate')
            executor = RootDeactivateExecutor(self._ainstRoot, 
                                              self._ainstConf,
                                              pkg,
                                              param.noStop,
                                              param.noExecute,
                                              dryrun=param.dryRun)
            compositeExecutor.appendExecutor(executor)
        if not param.dryRun:
            if not param.confirmYes and not Log.coutConfirm():
                return OperatorRet.OPERATE_SUCCESS
        if not compositeExecutor.execute():
            return OperatorRet.OPERATE_FAILED
        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS
        if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS


    def _doDeactivate(self, compositeExecutor, operations, topOrder,
                      param, keyValueList):
        for pkg in topOrder:
            if operations.has_key(pkg) and operations[pkg] == resolver.REMOVE:
                keyValueList.append(('%s' % pkg, 'deactivate'))
                executor = RootDeactivateExecutor(self._ainstRoot, 
                                                  self._ainstConf,
                                                  pkg,
                                                  param.noStop,
                                                  param.noExecute,
                                                  dryrun=param.dryRun)
                compositeExecutor.appendExecutor(executor)
        return True

    def remove(self, pkgs, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, 'Remove to invalid ainst root')
            return OperatorRet.OPERATE_FAILED

        if not pkgs:
            return OperatorRet.OPERATE_FAILED
        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         False)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        deactivatePkgs = self._selectInstalledPkgs(context, pkgs)
        keyValueList = []
        compositeExecutor = CompositeExecutor()
        if deactivatePkgs:
            resolverOption = ResolverOption()
            depResolver = RecursiveDepResolver(context, resolverOption)
            ret, operations, topOrder = depResolver.remove(deactivatePkgs)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, 'Dependency resovle failed')
                return OperatorRet.OPERATE_FAILED
            self._doDeactivate(compositeExecutor, operations, topOrder,
                               param, keyValueList)

        context = self._contextBuilder.buildLocalRemoveContext(self._installRoot)
        if context is None:
            Log.cout(Log.ERROR, 'Build local remove context failed')
            return OperatorRet.OPERATE_FAILED
        removePkgs = self._selectInstalledPkgs(context, pkgs)
        if not deactivatePkgs and not removePkgs:
            return OperatorRet.OPERATE_FAILED
        if not removePkgs:
            Log.coutValueList(Log.INFO, keyValueList)
            if not param.dryRun:
                if not param.confirmYes and not Log.coutConfirm():
                    return OperatorRet.OPERATE_SUCCESS
            if not compositeExecutor.execute():
                return OperatorRet.OPERATE_FAILED
            if not param.dryRun:
                if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
                    return OperatorRet.OPERATE_FAILED
            return OperatorRet.OPERATE_SUCCESS

        if not self._getRemoveExecutor(compositeExecutor, removePkgs, param,
                                       keyValueList, context):
            return OperatorRet.OPERATE_FAILED

        return self._executeRemove(param, compositeExecutor, keyValueList, command)

    def _executeRemove(self, param, compositeExecutor, keyValueList, command):
        Log.coutValueList(Log.INFO, keyValueList)
        if not param.dryRun:
            if not param.confirmYes and not Log.coutConfirm():
                return OperatorRet.OPERATE_SUCCESS
        if not compositeExecutor.execute():
            return OperatorRet.OPERATE_FAILED
        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS

        if compositeExecutor.isExecuted():
            saveExecutor = RootSaveExecutor(self._ainstRoot, 
                                            self._ainstConf,
                                            command)
            compositeExecutor.appendExecutor(saveExecutor)
            if not compositeExecutor.execute():
                Log.cout(Log.ERROR, 'Save root state failed')
                return OperatorRet.OPERATE_FAILED
            if not self._removeInstallRootFromRootInfo():
                Log.cout(Log.ERROR, 'Add install root to root info failed')
                compositeExecutor.undo()
                return OperatorRet.OPERATE_FAILED

        return OperatorRet.OPERATE_SUCCESS

    def _getRemoveExecutor(self, compositeExecutor, removePkgs, param,
                           keyValueList, context):
        if param.noDependents:
            for pkg in removePkgs:
                keyValueList.append(('%s' % pkg, 'remove'))
                executor = RootRemoveExecutor(self._ainstRoot, 
                                              self._ainstConf, pkg,
                                              dryrun=param.dryRun)
                compositeExecutor.appendExecutor(executor)
        else:
            resolverOption = ResolverOption()
            depResolver = RecursiveDepResolver(context, resolverOption)
            ret, operations, topOrder = depResolver.remove(removePkgs)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, 'Dependency resovle failed')
                return False
            for pkg in topOrder:
                if operations.has_key(pkg) and operations[pkg] == resolver.REMOVE:
                    keyValueList.append(('%s' % pkg, 'remove'))
                    executor = RootRemoveExecutor(self._ainstRoot, 
                                                  self._ainstConf,
                                                  pkg,
                                                  dryrun=param.dryRun)
                    compositeExecutor.appendExecutor(executor)
        return True

    def save(self, param, command):
        if not self._ainstRoot.isAvailableAinstRoot():
            Log.cout(Log.ERROR, 'Save to unavailable ainst root')
            return OperatorRet.OPERATE_FAILED

        saveExecutor = RootSaveExecutor(self._ainstRoot, self._ainstConf, 
                                        command, param.file)
        if not saveExecutor.execute():
            Log.cout(Log.ERROR, 'Save root state failed')
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def restore(self, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return OperatorRet.OPERATE_FAILED
        reader = AinstRootReader(self._ainstRoot)
        needRestore, restoreState = self._getRestoreRootState(reader, param)
        if not needRestore:
            Log.cout(Log.ERROR, 'Need not to restore')
            return OperatorRet.OPERATE_SUCCESS
        if not restoreState:
            Log.cout(Log.ERROR, 'Get root state failed')
            return OperatorRet.OPERATE_FAILED
        
        nowPkgSettings = reader.getPkgSettings()
        pkgSettings, unsetKeys = self._mergeSettings(restoreState.pkgSettings,
                                                     nowPkgSettings)
        restoreActivePkgs = [pkg for pkg, mtime in restoreState.activePkgs]
        nowActivePkgs = [pkgVer for pkgName, pkgVer, mtime in reader.getActivePackages()]
        compositeExecutor, keyValueList, willActivePkgs, willDeactivePkgs =\
            self._addActiveExecutorToRestore(reader, param, restoreActivePkgs,
                                             pkgSettings, unsetKeys)
        if compositeExecutor is None:
            return OperatorRet.OPERATE_FAILED

        activePkgs = self._mergeActivePkgs(nowActivePkgs, willActivePkgs, willDeactivePkgs)
        deactivatePkgs = []
        if activePkgs:
            for pkg in activePkgs:
                if pkg not in restoreActivePkgs:
                    deactivatePkgs.append(pkg)

        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         False,
                                                         localActivePkgs=willActivePkgs,
                                                         localDeactivePkgs=willDeactivePkgs)
        removePkgs = self._selectInstalledPkgs(context, deactivatePkgs)
        if not removePkgs:
            if not keyValueList:
                Log.cout(Log.INFO, 'No effective operations')
                return OperatorRet.OPERATE_SUCCESS
            Log.coutValueList(Log.INFO, keyValueList)
            if not param.dryRun:
                if not param.confirmYes and not Log.coutConfirm():
                    return OperatorRet.OPERATE_SUCCESS
            if not compositeExecutor.execute():
                return OperatorRet.OPERATE_FAILED
            if not param.dryRun:
                if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
                    return OperatorRet.OPERATE_FAILED                
            return OperatorRet.OPERATE_SUCCESS
        
        if not self._addDeactivateExecutorToRestore(context, removePkgs, param,
                                                    deactivatePkgs, keyValueList,
                                                    compositeExecutor):
            return OperatorRet.OPERATE_FAILED

        return self._executeRestore(param, keyValueList, compositeExecutor, command)

    def _executeRestore(self, param, keyValueList, compositeExecutor, command):
        Log.coutValueList(Log.INFO, keyValueList)
        if not param.dryRun:
            if not param.confirmYes and not Log.coutConfirm():
                return OperatorRet.OPERATE_SUCCESS

        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Restore pkgs failed')
            return OperatorRet.OPERATE_FAILED

        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS
        if not self._saveExecuted(compositeExecutor, self._ainstRoot, command):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS
        

    def _addDeactivateExecutorToRestore(self, context, removePkgs, param, 
                                        deactivatePkgs, keyValueList,
                                        compositeExecutor):
        removeDepResolver = RecursiveDepResolver(context, ResolverOption())
        removeRet, removeOps, removeOrder = removeDepResolver.remove(removePkgs)
        if removeRet != error.ERROR_NONE:
            Log.cout(Log.ERROR, 'Dependency resovle failed')
            return False

        for pkg in removeOrder:
            if removeOps.has_key(pkg) and removeOps[pkg] == resolver.REMOVE\
                    and PackageUtil.getPkgNameVersion(pkg) in deactivatePkgs:
                keyValueList.append(('%s' % pkg, 'deactivate'))
                executor = RootDeactivateExecutor(self._ainstRoot, 
                                                  self._ainstConf,
                                                  pkg,
                                                  dryrun=param.dryRun)
                compositeExecutor.appendExecutor(executor)
        return True

    def _addActiveExecutorToRestore(self, reader, param, restoreActivePkgs,
                                    pkgSettings, unsetKeys):
        willActivePkgs = []
        willDeactivePkgs = []
        keyValueList = []
        compositeExecutor = CompositeExecutor()
        if restoreActivePkgs:
            context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                             self._ainstConf,
                                                             True,
                                                             param.repos)
            if context is None:
                Log.cout(Log.ERROR, 'Build context failed')
                return None, None, None, None

            installPkgs = self._selectInstallPkgs(context, restoreActivePkgs)
            if not installPkgs:
                Log.cout(Log.ERROR, 'No package to install')
                return None, None, None, None

            if len(installPkgs) != len(restoreActivePkgs):
                Log.cout(Log.ERROR, 'Some pkgs are not available')
                return None, None, None, None

            resolverOption = ResolverOption()
            resolverOption.exclusiveDeps = False
            depResolver = RecursiveDepResolver(context, resolverOption)
            ret, operations, topOrder = depResolver.install(installPkgs)
            if ret != error.ERROR_NONE:
                Log.cout(Log.ERROR, 'Dependency resovle failed')
                return None, None, None, None

            willActive, willDeactive = self._getWillOperatePkgs(operations, topOrder)
            willActivePkgs.extend(willActive)
            willDeactivePkgs.extend(willDeactive)
            installedPkgs = reader.getInstallPackages()
            self._getActivateExecutor(compositeExecutor, operations, topOrder,
                                      param, installedPkgs, keyValueList,
                                      pkgSettings, unsetKeys)
        return compositeExecutor, keyValueList, willActivePkgs, willDeactivePkgs

    def _getRestoreRootState(self, rootReader, param):
        needRestore = True
        if not rootReader:
            return needRestore, None
        restoreState = None
        if not self._isValidRestoreOptions(param):
            Log.cout(Log.ERROR, 'Invalied Restore options')
            return needRestore, None
        if param.previous:
            restoreState = rootReader.getPreviousRootState()
        elif param.stateNumber is not None:
            if rootReader.isCurrentStateNumber(param.stateNumber):
                needRestore = False
            else:
                restoreState = rootReader.getRootStateByNumber(param.stateNumber)
        elif param.stateFile:
            restoreState = RootStateStreamer().getRootStateFromFile(param.stateFile)
        elif param.timeStr:
            timeStamp = time_util.timeStr2Stamp(param.timeStr)
            if timeStamp is None:
                return True, None
            restoreState = rootReader.getRootStateByTime(timeStamp)
        else:
            Log.cout(Log.ERROR, 'Invalied Restore options')
            return needRestore, None
        return needRestore, restoreState

    def _isValidRestoreOptions(self, param):
        optionList = [param.previous, param.stateNumber, param.stateFile, param.timeStr]
        optionCount = 0
        for option in optionList:
            if option is not None and option is not False:
                optionCount += 1
        if optionCount != 1:
            return False
        return True

    def _mergeSettings(self, restorePkgSettings, nowPkgSettings):
        resultSettings = {}
        resultSettings.update(restorePkgSettings)
        unsetKeys = {}
        for pkg, keyValue in nowPkgSettings.iteritems():
            if resultSettings.has_key(pkg):
                for key, value in keyValue.iteritems():
                    if not resultSettings[pkg].has_key(key):
                        unsetKeys.setdefault(pkg, set([])).add(key)
        return resultSettings, unsetKeys

    def _getWillOperatePkgs(self, operations, topOrder):
        willActivePkgs = []
        willDeactivePkgs = []
        for pkg in topOrder:
            if operations.has_key(pkg) and operations[pkg] == resolver.INSTALL:
                willActivePkgs.append(pkg)
            elif operations.has_key(pkg) and operations[pkg] == resolver.REMOVE:
                willDeactivePkgs.append(pkg)
        return willActivePkgs, willDeactivePkgs

    def _mergeActivePkgs(self, nowActivePkgs, willActivePkgs, willDeactivePkgs):
        activePkgs = []
        if nowActivePkgs:
            activePkgs.extend(nowActivePkgs)
        if willActivePkgs:
            for pkg in willActivePkgs:
                activePkgs.append(str(pkg))
        if willDeactivePkgs:
            for pkg in willDeactivePkgs:
                if str(pkg) in activePkgs:
                    activePkgs.remove(str(pkg))
        return activePkgs

    def _saveExecuted(self, compositeExecutor, ainstRoot, command):
        if compositeExecutor.isExecuted():
            saveExecutor = RootSaveExecutor(ainstRoot, self._ainstConf, command)
            compositeExecutor.appendExecutor(saveExecutor)
            if not compositeExecutor.execute():
                Log.cout(Log.ERROR, 'Save root state failed')
                return False
        return True        

    def start(self, pkgs, param, command):
        if not self._doActionExecutor(pkgs, param, 'start'):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def stop(self, pkgs, param, command):
        if not self._doActionExecutor(pkgs, param, 'stop'):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def restart(self, pkgs, param, command):
        if not self._doActionExecutor(pkgs, param, 'restart'):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def reload(self, pkgs, param, command): 
        if not self._doActionExecutor(pkgs, param, 'reload'):
            return OperatorRet.OPERATE_FAILED
        return OperatorRet.OPERATE_SUCCESS

    def _doActionExecutor(self, pkgs, param, action):
        installRoots = []
        if not self._installRoot:
            streamer = RootInfoDbStreamer()
            rootInfo = streamer.load(self._ainstConf.rootinfo)
            if rootInfo is None:
                Log.cout(Log.ERROR, 'Load root info failed')
                return OperatorRet.OPERATE_FAILED
            for root in rootInfo.installRootSet:
                installRoots.append(root)
            installRoots.append('/')
        else:
            installRoots.append(self._installRoot)

        context = self._contextBuilder.buildMultiRootContext(installRoots,
                                                             self._ainstConf)

        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        installedPkgs = self._selectInstalledPkgs(context, pkgs)
        if not installedPkgs:
            Log.cout(Log.ERROR, 'Get installed pkg failed')
            return False
        compositeExecutor = CompositeExecutor()
        for pkg in installedPkgs:
            ainstRoot = AinstRoot(pkg.repo.id)
            executor = globals()[self._actionDict[action]](ainstRoot, 
                                                           self._ainstConf, pkg,
                                                           param.dryRun)
            compositeExecutor.appendExecutor(executor)
        if not compositeExecutor.execute():
            Log.cout(Log.ERROR, 'Do action failed')
            return False
        return True

    def crontab(self, pkgs, param, command):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, 'Crontab to invalid ainst root')
            return OperatorRet.OPERATE_FAILED

        if not self._checkCrontabParam(param, pkgs):
            Log.cout(Log.ERROR, 'Crontab option illegal')
            return OperatorRet.OPERATE_FAILED

        if param.crontabList:
            if not self._crontabList(pkgs, param.crontabUser):
                Log.cout(Log.ERROR, 'Crontab list failed')
                return OperatorRet.OPERATE_FAILED
        elif param.crontabOn:
            if not self._crontabOn(pkgs, param.crontabUser):
                Log.cout(Log.ERROR, 'Crontab on failed')
                return OperatorRet.OPERATE_FAILED
        elif param.crontabOff:
            if not self._crontabOff(pkgs, param.crontabUser):
                Log.cout(Log.ERROR, 'Crontab off failed')
                return OperatorRet.OPERATE_FAILED                    
        return OperatorRet.OPERATE_SUCCESS

    def _crontabOn(self, installedPkgs, crontabUser=None):
        if not installedPkgs:
            return False

        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return False
        reader = AinstRootReader(self._ainstRoot)
        pkgCrontabs = reader.getPkgCrontabs()
        wrapper = CrontabWrapper()
        content = wrapper.getCrontab(crontabUser)
        if content is None:
            content = ''
        streamer = CrontabInfoStreamer()
        crontabInfo = streamer.parseCrontabInfo(content)
        
        needSet = False
        for pkgName in installedPkgs:
            keyTuple = (self._installRoot, pkgName)
            if crontabInfo.crontabDict.has_key(keyTuple):
                Log.cout(Log.INFO, 'Pkg %s crontab is already on' % pkgName)
            elif pkgCrontabs.has_key(pkgName):
                Log.cout(Log.INFO, 'Turn pkg %s crontab on' % pkgName)
                content = streamer.addCrontabItem(content, self._installRoot,
                                                  pkgName, pkgCrontabs[pkgName])
                needSet = True
            else:
                Log.cout(Log.INFO, 'Pkg %s has no crontab' % pkgName)

        if not needSet:
            return True
        return wrapper.setCrontabString(content, crontabUser)

    def _crontabOff(self, installedPkgs, crontabUser=None):
        if not installedPkgs:
            return False

        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return False
        reader = AinstRootReader(self._ainstRoot)
        pkgCrontabs = reader.getPkgCrontabs()
        wrapper = CrontabWrapper()
        content = wrapper.getCrontab(crontabUser)
        if content is None:
            content = ''
        streamer = CrontabInfoStreamer()
        crontabInfo = streamer.parseCrontabInfo(content)
        
        needSet = False
        for pkgName in installedPkgs:
            keyTuple = (self._installRoot, pkgName)
            if crontabInfo.crontabDict.has_key(keyTuple):
                Log.cout(Log.INFO, 'Turn Pkg %s crontab off' % pkgName)
                content = streamer.cutCrontabItem(content,
                                                  self._installRoot, pkgName)
                needSet = True
            elif pkgCrontabs.has_key(pkgName):
                Log.cout(Log.INFO, 'Pkg %s crontab is already off' % pkgName)
            else:
                Log.cout(Log.INFO, 'Pkg %s has no crontab' % pkgName)

        if not needSet:
            return True
        return wrapper.setCrontabString(content, crontabUser) 

    def _crontabList(self, installedPkgs, crontabUser=None):
        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return False
        reader = AinstRootReader(self._ainstRoot)
        pkgCrontabs = reader.getPkgCrontabs()
        content = CrontabWrapper().getCrontab(crontabUser)
        if content is None:
            content = ''
        crontabInfo = CrontabInfoStreamer().parseCrontabInfo(content)
        if not installedPkgs:
            for pkgName, crontab in pkgCrontabs.items():
                if crontabInfo.crontabDict.has_key((self._installRoot, pkgName)):
                    Log.coutLabel(Log.INFO, 'Pkg %s crontab on' % pkgName)
                    Log.cout(Log.INFO, crontabInfo.crontabDict[(self._installRoot, pkgName)])
                elif pkgCrontabs.has_key(pkgName):
                    Log.coutLabel(Log.INFO, 'Pkg %s crontab off' % pkgName)
                    Log.cout(Log.INFO, pkgCrontabs[pkgName])
            return True

        for pkgName in installedPkgs:
            if crontabInfo.crontabDict.has_key((self._installRoot, pkgName)):
                Log.coutLabel(Log.INFO, 'Pkg %s crontab on' % pkgName)
                Log.cout(Log.INFO, crontabInfo.crontabDict[(self._installRoot, pkgName)])
            elif pkgCrontabs.has_key(pkgName):
                Log.coutLabel(Log.INFO, 'Pkg %s crontab off' % pkgName)
                Log.cout(Log.INFO, pkgCrontabs[pkgName])
            else:
                Log.coutLabel(Log.INFO, 'Pkg %s has no crontab' % pkgName)
        return True

    def _checkCrontabParam(self, param, pkgs):
        optionCount = 0
        if param.crontabOn:
            optionCount += 1
        if param.crontabOff:
            optionCount += 1
        if param.crontabList:
            optionCount += 1
        if optionCount != 1:
            return False
        if not param.crontabList and len(pkgs) < 1:
            return False
        return True

if __name__ == '__main__':
    pass
