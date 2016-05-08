#! /usr/bin/python

import os
import rpm
import error
import rpmutils
import resolver
from logger import Log
from cache_handler import RepoCacheHandler
from root_info import RootInfoDbStreamer
from ainst_context import AinstContextBuilder
from resolver import RecursiveDepResolver, ResolverOption
from ainst_operator import AinstOperator, OperatorRet

class RootAinstOperator(AinstOperator):
    def __init__(self, ainstConf, installRoot):
        AinstOperator.__init__(self, ainstConf)
        self._installRoot = installRoot
        self._contextBuilder = AinstContextBuilder()

    def install(self, pkgs, param, command):
        streamer = RootInfoDbStreamer()
        rootInfo = streamer.load(self._ainstConf.rootinfo)
        if rootInfo is None:
            Log.cout(Log.ERROR, 'Load root info failed')
            return OperatorRet.OPERATE_FAILED
        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         True,
                                                         param.repos,
                                                         param.localRepos,
                                                         localRoots=rootInfo.installRootSet)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        installPkgs = self._selectInstallPkgs(context, pkgs)
        if not installPkgs:
            Log.cout(Log.INFO, 'No package to install')
            return OperatorRet.OPERATE_FAILED

        resolverOption = self._getResolverOption(param)
        depResolver = RecursiveDepResolver(context, resolverOption)
        ret, operations, topOrder = depResolver.install(installPkgs)
        if ret != error.ERROR_NONE:
            Log.cout(Log.ERROR, 'Dependency resovle failed')
            return OperatorRet.OPERATE_FAILED
        if not operations:
            Log.cout(Log.INFO, 'No effective operations')
            return OperatorRet.OPERATE_SUCCESS
        
        self._displayOperations(operations)
        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS

        if not param.confirmYes and not Log.coutConfirm():
            return True
        if not self._doRpmTransaction(operations):
            Log.cout(Log.ERROR, 'Do rpm transaction failed')
            return OperatorRet.OPERATE_FAILED

        return OperatorRet.OPERATE_SUCCESS

    def _getResolverOption(self, param):
        resolverOption = ResolverOption()
        if param.check:
            resolverOption.checkType = ResolverOption.CHECK_INSTALLED
        if param.downgrade:
            resolverOption.downgrade = True
        if param.noUpgrade:
            resolverOption.upgrade = False
        if param.noExclusive:
            resolverOption.exclusiveDeps = False
        return resolverOption

    def _displayOperations(self, operations):
        for pkg, action in operations.iteritems():
            if action == resolver.INSTALL:
                Log.coutValue(Log.INFO, '%s' % pkg, 'install')
            elif action == resolver.REMOVE:
                Log.coutValue(Log.INFO, '%s' % pkg, 'remove')

    def _doRpmTransaction(self, operations, noDependents=False):
        ts = rpm.TransactionSet()
        for pkg, action in operations.iteritems():
            if action == resolver.INSTALL:
                pkgPath = self._getRpmFilePath(pkg)
                if not pkgPath:
                    Log.cout(Log.ERROR, 'Get pkg %s failed' % pkg)
                    return False
                header = rpmutils.readRpmHeader(pkgPath)
                if header is None:
                    Log.cout(Log.ERROR, 'Get pkg %s header failed' % pkg)
                    return False
                ts.addInstall(header, pkgPath, 'u')
            elif action == resolver.REMOVE:
                ts.addErase(str(pkg))
        unresolved = None
        if not noDependents:
            unresolved = ts.check()
        if not unresolved:
            ts.order()
            pkgDict = {}
            try:
                flags = rpm.RPMPROB_FILTER_OLDPACKAGE |\
                    rpm.RPMPROB_FILTER_REPLACEPKG
                ts.setProbFilter(flags)
                tsError = ts.run(self._runCallback, pkgDict)
                if tsError is None:
                    return True
                Log.cout(Log.ERROR, 'Transaction run failed:%s' % tsError)
                return False
            except Exception, e:
                Log.cout(Log.ERROR, 'Rpm Transaction run failed:%s' % e)
                return False
            return True
        else:
            Log.cout(Log.ERROR, 'Rpm Transaction check failed:%s' % unresolved)
            return False

    def _getRpmFilePath(self, pkg):
        location = pkg.getLocation()
        if not location:
            return None
        rpmFilePath = location
        if location.lower().startswith('http'):
            cacheHandler = RepoCacheHandler(pkg.repo.id, None, 
                                            self._ainstConf.cachedir, 
                                            self._ainstConf.expiretime,
                                            self._ainstConf.maxfilelength,
                                            self._ainstConf.retrytime,
                                            self._ainstConf.sockettimeout)
            rpmFilePath = cacheHandler.getPackage(pkg)
            if rpmFilePath is None:
                Log.cout(Log.ERROR, 'Get Package %s failed' % pkg)
        return rpmFilePath

    def _runCallback(self, reason, amount, total, key, client_data):
        if reason == rpm.RPMCALLBACK_INST_OPEN_FILE:
            client_data[key] = os.open(key, os.O_RDONLY)
            return client_data[key]
        elif reason == rpm.RPMCALLBACK_INST_START:
            os.close(client_data[key])

    def remove(self, pkgs, param, command):
        streamer = RootInfoDbStreamer()
        rootInfo = streamer.load(self._ainstConf.rootinfo)
        if rootInfo is None:
            Log.cout(Log.ERROR, 'Load root info failed')
            return OperatorRet.OPERATE_FAILED
        context = self._contextBuilder.buildAinstContext(self._installRoot,
                                                         self._ainstConf,
                                                         False,
                                                         localRoots=rootInfo.installRootSet)
        if context is None:
            Log.cout(Log.ERROR, 'Build context failed')
            return OperatorRet.OPERATE_FAILED

        removePkgs = self._selectInstalledPkgs(context, pkgs)
        if not removePkgs:
            Log.cout(Log.ERROR, 'No package to remove')
            return OperatorRet.OPERATE_FAILED
        
        operations = self._getRemoveOperations(param, context, removePkgs)
        if operations is None:
            return OperatorRet.OPERATE_FAILED

        if not operations:
            Log.cout(Log.INFO, 'No effective operations')
            return OperatorRet.OPERATE_SUCCESS
        
        self._displayOperations(operations)
        if param.dryRun:
            return OperatorRet.OPERATE_SUCCESS

        if not param.confirmYes and not Log.coutConfirm():
            return OperatorRet.OPERATE_SUCCESS

        if not self._doRpmTransaction(operations, param.noDependents):
            Log.cout(Log.ERROR, 'Do rpm transaction failed')
            return OperatorRet.OPERATE_FAILED

        return OperatorRet.OPERATE_SUCCESS

    def _getRemoveOperations(self, param, context, removePkgs):
        if param.noDependents:
            operations = {}
            for pkg in removePkgs:
                if pkg:
                    operations[pkg] = resolver.REMOVE
            return operations

        resolverOption = ResolverOption()
        depResolver = RecursiveDepResolver(context, resolverOption)
        ret, operations, topOrder = depResolver.remove(removePkgs)
        if ret != error.ERROR_NONE:
            Log.cout(Log.ERROR, 'Dependency resovle failed')
            return None
        return operations

    def list(self, pkgs, param, command):
        if len(pkgs) > 1:
            return OperatorRet.OPERATE_FAILED
        context = self._contextBuilder.buildMultiRootContext([self._installRoot],
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
                self._printPkgFiles(pkg, param, indents * 2)
            Log.cout(Log.INFO, '')
        return OperatorRet.OPERATE_SUCCESS

    def _printPkgFiles(self, pkg, param, indents):
        if not param.files or not hasattr(pkg, 'files'):
            return
        Log.cout(Log.INFO, " " * indents + "Files: ")
        for fileName in pkg.files:
            Log.cout(Log.INFO, " " * indents * 2 + "%s" % fileName)

    def activate(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Activate is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def deactivate(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Deactivate is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def start(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Start is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def stop(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Stop is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def restart(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Restart is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def reload(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Reload is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def save(self, param, command):
        Log.cout(Log.ERROR, 'Save is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def restore(self, param, command):
        Log.cout(Log.ERROR, 'Restore is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def set(self, param, command):
        Log.cout(Log.ERROR, 'Set is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def history(self, param, command):
        Log.cout(Log.ERROR, 'History is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT

    def crontab(self, pkgs, param, command):
        Log.cout(Log.ERROR, 'Crontab is not supported in root dir')
        return OperatorRet.OPERATE_NOT_SUPPORT
