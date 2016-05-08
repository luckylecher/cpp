#! /usr/bin/python

import sys
from ainst_command import *

class Ainst:
    def __init__(self):
        self._commands = []
        self._cmdMap = {}

    def process(self, argv):
        self._initCommands()
        if len(argv) < 1:
            print self._makeUsage()
            return False
        cmd = None
        cmdStr = argv[0]
        if self._cmdMap.has_key(cmdStr):
            cmd = self._cmdMap[cmdStr]
        else:
            print self._makeUsage()
            return False

        if not cmd.execute(argv[1:]):
            return False
            
        return True

    def _initCommands(self):
        self._registerCommands(AinstInstallCommand())
        self._registerCommands(AinstActivateCommand())
        self._registerCommands(AinstDeactivateCommand())
        self._registerCommands(AinstRemoveCommand())
        self._registerCommands(AinstStartCommand())
        self._registerCommands(AinstStopCommand())
        self._registerCommands(AinstRestartCommand())
        self._registerCommands(AinstReloadCommand())
        self._registerCommands(AinstSaveCommand())
        self._registerCommands(AinstRestoreCommand())
        self._registerCommands(AinstMakeCacheCommand())
        self._registerCommands(AinstClearCacheCommand())
        self._registerCommands(AinstSetCommand())
        self._registerCommands(AinstHistoryCommand())
        self._registerCommands(AinstListCommand())
        self._registerCommands(AinstCrontabCommand())

    def _registerCommands(self, command):
        self._commands.append(command)
        for name in command.getNames():
            self._cmdMap[name] = command

    def _makeUsage(self):
        usage = 'Usage:\nainst2 cmd [options]\n\nList of Commands:\n'
        usageList = []
        for command in self._commands:
            names = command.getNames()
            cmdstr = names[0]
            if len(names) > 1:
                cmdstr += ' (' 
            for name in names[1:]:
                cmdstr += name + ','
            if len(names) > 1:
                cmdstr = cmdstr[:-1]
                cmdstr += ')' 
            usageList.append("%-40s %s\n" % (cmdstr, command.getSummary()))
        for use in usageList:
            usage += use
        return usage


if __name__ == '__main__':
    ainst = Ainst()
    if ainst.process(sys.argv[1:]):
        sys.exit(0)
    sys.exit(1)
