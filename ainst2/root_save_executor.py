#! /usr/bin/python

import time
from logger import Log
import common
import file_util
from root_state import RootState, RootStateStreamer
from ainst_root import AinstRoot, AinstRootReader
from setting_streamer import SettingStreamer
from root_executor import RootExecutor

class RootSaveExecutor(RootExecutor):
    def __init__(self, ainstRoot, ainstConf, command, saveFile=None):
        RootExecutor.__init__(self, ainstRoot, ainstConf)
        self._command = command
        self._saveFile = saveFile
        self._executed = False
        self._stateFileName = None

    def execute(self):
        if self._executed:
            return False
        self._executed = True

        Log.cout(Log.INFO, 'Save root state...')

        if not self._ainstRoot.checkRoot():
            Log.cout(Log.ERROR, 'Check ainst root failed')
            return False

        saveDir = self._ainstRoot.getRootVarAinstDir('save')
        settingsDir = self._ainstRoot.getRootVarAinstDir('settings')
        tmpDir = self._ainstRoot.getRootVarAinstDir('tmp')
        if not saveDir or not settingsDir or not tmpDir:
            Log.cout(Log.ERROR, 'There is not save, settings or tmp dir in installroot')
            return False

        if not self._ainstRoot.isValidAinstRoot():
            Log.cout(Log.ERROR, '%s is invalid ainst root' % self._ainstRoot.getRoot())
            return False
        reader = AinstRootReader(self._ainstRoot)
        activePkgs = reader.getActivePackages()
        activePkgNames = [pkgName for pkgName, pkgVer, mtime in activePkgs]
        activePkgInfos = [(pkgVer, mtime) for pkgName, pkgVer, mtime in activePkgs]
        activePkgInfos = sorted(activePkgInfos, key = lambda pkg : pkg[1])
        pkgSettings = reader.getPkgSettings(activePkgNames)

        state = RootState(time.time(), self._command, self._ainstRoot.getRoot(),
                          common.AINST_VERSION, activePkgInfos, pkgSettings)
        content = RootStateStreamer().toString(state)
        if not content:
            Log.cout(Log.ERROR, 'Generate root state content failed')
            return False
            
        stateFileName = reader.getNextStateFileName()
        self._tmpFile = tmpDir + stateFileName
        if not file_util.writeToFile(self._tmpFile, content):
            Log.cout(Log.ERROR, 'Write state to %s failed' % self._tmpFile)
            return False

        saveFile = saveDir + stateFileName
        if self._saveFile:
            saveFile = self._saveFile

        if not file_util.move(self._tmpFile, saveFile):
            Log.cout(Log.ERROR, 'Move root state file %s failed' % saveFile)
            self.undo()
            return False

        self._stateFileName = saveFile
        return True

    def undo(self):
        if not self._executed:
            return False

        if self._stateFileName:
            file_util.remove(self._stateFileName)

        if self._tmpFile:
            file_util.remove(self._tmpFile)

        self._executed = False
        return True

