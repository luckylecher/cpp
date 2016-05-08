#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import re
import random
import signal
import os
import subprocess

TIMEOUT_INTERVAL = 0.05

class Process:
    def __init__(self, p, outfile=None, errfile=None):
        self.p = p
        self.outfile = outfile
        self.errfile = errfile

    def communicate(self, timeout=0):
        self.__waitProcess(timeout)
        stdout, stderr = self.p.communicate()
        outResult, errResult = stdout, stderr
        if self.outfile:
            self.outfile.seek(0)
            outResult = self.outfile.read()
            self.outfile.close()
        if self.errfile:
            self.errfile.seek(0)
            errResult = self.errfile.read()
            self.errfile.close()
        return (outResult, errResult, self.p.returncode)

    def __waitProcess(self, timeout):
        if timeout <= 0:
            self.p.wait()
        while timeout > 0:
            if self.p.poll() != None:
                break
            time.sleep(TIMEOUT_INTERVAL)
            timeout = timeout - TIMEOUT_INTERVAL
        if self.p.poll() == None:
            self.kill()

    def terminated(self):
        return self.p.poll() != None

    def kill(self, sig = signal.SIGKILL):
        pidset = set()
        pidList = list()
        pidList.append(self.p.pid)
        index = 0
        while index < len(pidList):
            subPidList = self.__getSubPidList(pidList[index])
            for subPid in subPidList:
                if subPid not in pidset:
                    pidList.append(subPid)
                    pidset.add(subPid)
            index += 1
        self.__killPidList(sig, pidList)
        self.p.wait()
        return True

    def __getSubPidList(self, pid):
        pidList = []
        pattern = re.compile('\s+')
        result = os.popen('ps -ef | grep %d' % pid).read()
        lines = result.strip().split('\n')
        for line in lines:
            line = pattern.split(line.strip())
            if str(pid) == line[2]:
                pidList.append(int(line[1]))
        return pidList

    def __killPidList(self, sig, pidList):
        for pid in pidList:
            try:
                os.kill(int(pid), sig)
            except OSError:
                continue
        

def start(cmd):
    p = __popen(cmd, subprocess.PIPE, subprocess.PIPE)
    return Process(p)

def startRedirected(cmd):
    outfile = os.tmpfile()
    errfile = os.tmpfile()
    p = __popen(cmd, outfile, errfile)
    process = Process(p, outfile, errfile)
    return process

def run(cmd, timeout=0):
    process = start(cmd)
    return process.communicate(timeout)

def runRedirected(cmd, timeout=0):
    process = startRedirected(cmd)
    return process.communicate(timeout)

def __popen(cmd, outfile, errfile):
    p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=errfile)
    return p

if __name__ == '__main__':
    cmd = 'crontab -l -u larmmi.zhang'
    out, err, code = run(cmd, 10)
    print code
    print err
    print out
    

#    cmd = './bin/http_load -s 20 -p 20 -cmd post ./test_data/q.1.in'
#    out, err, code = runRedirected(cmd, 40)
#    out, err, code = run(cmd, 40)
#    print len(err)
#    print out

#    process = startRedirected(cmd)
#    out, err, code = process.communicate(40)
#    print out

#    process = start(cmd)
#    time.sleep(3)
#    process.kill()
#    os.kill(process.p.pid, signal.SIGKILL)
#    time.sleep(5)
#    print process.p.poll()
        
#    out, err, code = process.communicate(40)
#    print out

#    cmd = 'python ./test_common.py'
#    process = start(cmd)
#    time.sleep(6)
#    process.killAll()
