#! /usr/bin/python

import os
import re
import time
import getpass 
import process
import file_util
import threading
from logger import Log
from host_expander import HostExpander

class RemoteExecutor:
    def __init__(self):
        self._killTimeout = 120

    def remoteExecute(self, host, executorPath, remoteCmd, remoteUser,
                      remoteTimeout=1200, retryTime=0, retryInterval=0,
                      remoteSudo=False):
        while True:
            begin = time.time()
            Log.cout(Log.INFO, remoteCmd)
            out, err, code = process.runRedirected(remoteCmd, remoteTimeout)
            end = time.time()
            Log.cout(Log.INFO, out)
            if code == 0:
                Log.coutValue(Log.INFO, 'Process Remote host %s' % host, 'success')
                return True
            Log.cout(Log.ERROR, err)
            if end - begin >= remoteTimeout:
                Log.coutValue(Log.ERROR, 'Process Remote host %s' % host, 'timeout')
                self._killRemoteCmd(host, executorPath, remoteCmd, remoteUser, remoteSudo)
            else:
                Log.coutValue(Log.ERROR, 'Process Remote host %s' % host, 'failed')
            retryTime -= 1
            if retryTime < 0:
                break
            time.sleep(retryInterval)

        return False

    def _killRemoteCmd(self, host, executorPath, cmdStr, remoteUser, remoteSudo):
        pathIndex = cmdStr.find(executorPath)
        if pathIndex == -1:
            return False
        rawCmd = cmdStr[pathIndex:]
        rawCmd = ' '.join(rawCmd.split())
        Log.cout(Log.INFO, 'kill ainst2 process on the remote host %s ...' % host)
        cmd = 'ssh %s@%s ps -efw | grep \'%s\' | grep -v \'ssh %s@%s\' | grep -v grep'\
            % (remoteUser, host, rawCmd, remoteUser, host)
        out, err, code = process.runRedirected(cmd, self._killTimeout)
        if code != 0:
            Log.cout(Log.ERROR, 'get remote pid failed')
            return False

        pidList = []
        contentList = out.split('\n')
        for content in contentList:
            if not content or not content.strip():
                continue
            items = content.split()
            pidList.append(items[1])
        if not pidList:
            return True

        pidSet = set(pidList)
        index = 0
        while index < len(pidList):
            subPidList = self._getSubPidList(remoteUser, host, pidList[index])
            for subPid in subPidList:
                if subPid not in pidSet:
                    pidList.append(subPid)
                    pidSet.add(subPid)
            index += 1

        return self._killRemotePid(pidList, remoteUser, host, remoteSudo)

    def _killRemotePid(self, pidList, remoteUser, host, remoteSudo):
        hasFailed = False
        for pid in pidList:
            cmd = 'kill -9 %s' % pid
            if remoteSudo:
                cmd = 'sudo ' + cmd
            cmd = 'ssh %s@%s %s' % (remoteUser, host, cmd)
            Log.cout(Log.INFO, cmd)
            out, err, code = process.runRedirected(cmd, self._killTimeout)
            if code != 0:
                Log.cout(Log.ERROR, 'kill host %s process %s failed: %s'\
                             % (host, pid, err))
                hasFailed = True
        if hasFailed:
            return False
        return True

    def _getSubPidList(self, remoteUser, host, pid):
        pidList = []
        pattern = re.compile('\s+')
        out, err, code = process.runRedirected('ssh %s@%s ps -efw | grep %s'\
                                 % (remoteUser, host, pid), self._killTimeout)
        if code != 0:
            Log.cout(Log.ERROR, 'Get host %s process %s sub process failed: %s'\
                         % (host, pid, err))
            return pidList
        lines = out.strip().split('\n')
        for line in lines:
            line = pattern.split(line.strip())
            if str(pid) == line[2]:
                pidList.append(int(line[1]))
        return pidList
    
class RemoteOperatorThread(threading.Thread):
    def __init__(self, host, executorPath, cmd, timeout, retryTime,
                 retryInterval, remoteUser, remoteSudo):
        threading.Thread.__init__(self)
        self.executor = RemoteExecutor()
        self.returnValue = False
        self.host = host
        self.executorPath = executorPath
        self.cmd = cmd
        self.timeout = timeout
        self.retryTime = retryTime
        self.retryInterval = retryInterval
        self.remoteUser = remoteUser
        self.remoteSudo = remoteSudo

    def run(self):
        self.returnValue = \
            self.executor.remoteExecute(self.host, self.executorPath, self.cmd,
                                        self.remoteUser, self.timeout,
                                        self.retryTime, self.retryInterval,
                                        self.remoteSudo)
            
class RemoteOperator:
    def __init__(self):
        self._maxPallrel = 2000
        self._ainstBinPath = self._getAinstBinPath()

    def remoteOperate(self, param, command, installRoot=None, confirmYes=False):
        if param.remoteTimeout < 0 or param.retryInterval < 0:
            Log.cout(Log.ERROR, 'Remote param is invalid')
            return False

        if param.remoteBin:
            self._ainstBinPath = param.remoteBin

        hostSet = self._getHostSet(param.host, param.hostFile)
        if hostSet:
            hostSet = set([x for x in hostSet if x and x.strip()])
        if not hostSet:
            Log.cout(Log.ERROR, 'No valid ip or host')
            return False

        user = param.remoteUser
        if not user:
            user = getpass.getuser()
        cmd = self._generateRemoteCmd(command, confirmYes, installRoot,
                                      param.remoteConf)
        if param.remoteSudo:
            cmd = 'sudo %s' % cmd

        Log.coutLabel(Log.INFO, 'Process total %d remote host' % len(hostSet))
        parallel = self._getParallelCount(param.parallel)
        successList, failedList =\
            self._doParallelOperate(hostSet, cmd, parallel, param.remoteTimeout,
                                    param.retryTime, param.retryInterval,
                                    user, param.remoteSudo, param.errorContinue)

        Log.coutLabel(Log.INFO, 'Process remote host total(%d), success(%d), failed(%d)'\
                          % (len(hostSet), len(successList), len(failedList)))
        for success in successList:
            Log.coutValue(Log.INFO, success, 'success')
        for failed in failedList:
            Log.coutValue(Log.INFO, failed, 'failed')
        Log.coutLabel(Log.INFO, 'end')
        if len(failedList) > 0:
            return False
        return True

    def _getAinstBinPath(self):
        curPath = os.path.split(os.path.realpath(__file__))[0]
        return self._doGetAinstBinPath(curPath)
    
    def _doGetAinstBinPath(self, curPath):
        ainstInstRoot = ""
        pos = curPath.find("/usr/lib")
        if pos <= 0:
            ainstInstRoot = "/"
        else:
            ainstInstRoot = curPath[0:pos]
        return os.path.join(ainstInstRoot, "usr/bin/ainst2")

    def _getParallelCount(self, parallel):
        count = parallel
        if count > self._maxPallrel:
            count = self._maxPallrel
        if count < 1:
            count = 1
        return count

    def _doParallelOperate(self, hostSet, cmd, parallel, remoteTimeout, retryTime,
                           retryInterval, user, remoteSudo, errorContinue):
        successList = []
        failedList = []
        if not hostSet:
            return successList, failedList

        count = 0
        hostLen = len(hostSet)
        threaderList = []
        for host in hostSet:
            Log.coutLabel(Log.INFO, 'Process Remote host:%s' % host)
            remoteCmd = 'ssh %s@%s %s' % (user, host, cmd)
            threader = RemoteOperatorThread(host, self._ainstBinPath, remoteCmd,
                                            remoteTimeout, retryTime,
                                            retryInterval, user, remoteSudo)
            threader.setDaemon(True)
            threaderList.append(threader)
            threader.start()
            count += 1
            if count % parallel != 0 and count < hostLen:
                continue
            
            for threader in threaderList:
                threader.join()
            for threader in threaderList:
                if not threader.returnValue:
                    failedList.append(threader.host)
                else:
                    successList.append(threader.host)
            if not errorContinue and len(failedList) > 0:
                break
            threaderList = []

        return successList, failedList

    def _getHostSet(self, host, hostFile):
        itemList = []
        if hostFile:
            for fileName in hostFile:
                content = file_util.readFromFile(fileName)
                if content is None:
                    Log.cout(Log.ERROR, 'Invaild hostfile %s' % fileName)
                    return None
                itemList.extend(content.split())
        if host:
            resultList = self._splitHost(host)
            if resultList:
                itemList.extend(resultList)
        ipSet = set()
        expander = HostExpander()
        for item in itemList:
            if not item or not item.strip():
                continue
            hostList = expander.expand(item.strip())
            if hostList:
                ipSet.update(set(hostList))
        return ipSet

    def _splitHost(self, host):
        resultList = []
        if not host:
            return resultList

        curIndex = 0
        semicolonBegin = 0
        braceBegin = 0
        for index in range(len(host)):
            char = host[index]
            if char == '[':
                semicolonBegin += 1
            elif char == ']' and semicolonBegin > 0:
                semicolonBegin -= 1
            elif char == '{':
                braceBegin += 1
            elif char == '}' and braceBegin > 0:
                braceBegin -= 1
            elif char == ',' and semicolonBegin == 0 and braceBegin == 0:
                resultList.append(host[curIndex:index])
                curIndex = index + 1
        if curIndex < len(host):
            resultList.append(host[curIndex:])
        return resultList

    def _generateRemoteCmd(self, command, confirmYes, installRoot=None, remoteConf=None):
        cmd = command
        cmd = re.sub('\s+--host=\S+', '', cmd)
        cmd = re.sub('\s+--hostfile=\S+', '', cmd)
        cmd = re.sub('\s+--remotetimeout=\S+', '', cmd)
        cmd = re.sub('\s+--continue', '', cmd)
        cmd = re.sub('\s+--parallel=\S+', '', cmd)
        cmd = re.sub('\s+-p\s+\S+', '', cmd)
        cmd = re.sub('\s+--remoteuser=\S+', '', cmd)
        cmd = re.sub('\s+--remotebin=\S+', '', cmd)
        cmd = re.sub('\s+--remoteconf=\S+', '', cmd)
        cmd = re.sub('\s+--remotesudo', '', cmd)
        cmd = re.sub('\s+--retrytime=\S+', '', cmd)
        cmd = re.sub('\s+--retryinterval=\S+', '', cmd)
        
        if installRoot is not None:
            if re.search('\s+--installroot=', cmd):
                cmd = re.sub('\s+--installroot=\S+', ' --installroot=%s' % installRoot, cmd)
            else:
                cmd += ' --installroot=%s' % installRoot

        if remoteConf is not None:
            if re.search('\s+-c\s+', cmd):
                cmd = re.sub('\s+-c\s+\S+', ' -c %s' % remoteConf, cmd)
            else:
                cmd += ' -c %s' % remoteConf
            
        cmd = '%s %s' % (self._ainstBinPath, cmd)
        if confirmYes and not re.search('\s+--yes', cmd)\
                and not re.search('\s+-y', cmd):
            cmd += ' --yes'
        return cmd
