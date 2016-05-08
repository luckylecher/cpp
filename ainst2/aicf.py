#! /usr/bin/python

import file_util
from logger import Log

class AicfConfigMode:
    NONE_MODE = 0
    EXPAND_MODE = 1
    TEMPLATE_MODE = 2

class AicfConfigInfo:
    def __init__(self):
        self.destPath = None
        self.mode = AicfConfigMode.NONE_MODE
        self.noReplace = False

class AicfInfo:
    def __init__(self):
        self.autoStart = False
        self.settings = {}
        self.unSettings = set()
        self.crontabs = []
        self.configs = {}
        self.scripts = {}

class AicfParser:
    def __init__(self):
        self._scriptSet = (['pre-activate', 'post-activate', 'pre-deactivate', 
                            'post-deactivate', 'start', 'stop', 'restart',
                            'reload', 'boot', 'shutdown'])

    def parse(self, fileName):
        content = file_util.readFromFile(fileName)
        if content is None:
            Log.cout(Log.ERROR, 'Read aicf file [%s] failed' % fileName)
            return None

        aicfInfo = AicfInfo()
        lines = content.split('\n')
        for line in lines:
            line =  line.strip()
            if line == '' or line.startswith('#'):
                continue
            items = line.split()
            if items[0] == 'set':
                if not self._parseSettings(aicfInfo, items[1:]):
                    Log.cout(Log.ERROR, 'Parse aicf settings failed [%s]' % fileName)
                    return None
            elif items[0] == 'unset':
                if not self._parseUnSettings(aicfInfo, items[1:]):
                    Log.cout(Log.ERROR, 'Parse aicf unsettings failed [%s]' % fileName)
                    return None
            elif items[0] == 'autostart':
                if not self._parseAutoStart(aicfInfo, items[1:]):
                    Log.cout(Log.ERROR, 'Parse aicf autostart failed [%s]' % fileName)
                    return None
            elif items[0] == 'crontab':
                if not self._parseCrontabs(aicfInfo, items[1:]):
                    Log.cout(Log.ERROR, 'Parse aicf crontabs failed [%s]' % fileName)
                    return None
            elif items[0] == 'config':
                if not self._parseConfigs(aicfInfo, items[1:]):
                    Log.cout(Log.ERROR, 'Parse aicf config failed [%s]' % fileName)
                    return None
            elif items[0] == 'script':
                if not self._parseScripts(aicfInfo, items[1:]):
                    Log.cout(Log.ERROR, 'Parse aicf script failed [%s]' % fileName)
                    return None
            else:
                Log.cout(Log.ERROR, 'Parse aicf failed: illegal fields [%s]' % fileName)
                return None
        return aicfInfo

    def _parseSettings(self, aicfInfo, items):
        if len(items) != 2:
            return False
        aicfInfo.settings[items[0]] = items[1]
        return True

    def _parseUnSettings(self, aicfInfo, items):
        if len(items) != 1:
            return False
        aicfInfo.unSettings.add(items[0])
        return True

    def _parseAutoStart(self, aicfInfo, items):
        if len(items) != 1:
            return False
        if items[0] == 'on':
            aicfInfo.autoStart = True
        return True

    def _parseCrontabs(self, aicfInfo, items):
        if len(items) == 0:
            return False
        crontab = ' '.join(items)
        aicfInfo.crontabs.append(crontab)
        return True

    def _parseConfigs(self, aicfInfo, items):
        length = len(items)
        if length < 1 or length > 3:
            return False

        configInfo = AicfConfigInfo()        
        configInfo.destPath = items[0]

        if length == 2:
            if items[1] == 'noreplace':
                configInfo.noReplace = True
            elif items[1] == 'expand':
                configInfo.mode = AicfConfigMode.EXPAND_MODE
            elif items[1] == 'template':
                configInfo.mode = AicfConfigMode.TEMPLATE_MODE
            else:
                return False

        elif length == 3:
            if items[1] == 'expand':
                configInfo.mode = AicfConfigMode.EXPAND_MODE
            elif items[1] == 'template':
                configInfo.mode = AicfConfigMode.TEMPLATE_MODE
            else:
                return False
            if items[2] == 'noreplace':
                configInfo.noReplace = True
            else:
                return False
        aicfInfo.configs[configInfo.destPath] = configInfo
        return True

    def _parseScripts(self, aicfInfo, items):
        if len(items) < 2:
            return False
        if items[0] not in self._scriptSet:
            return False
        aicfInfo.scripts[items[0]] = ' '.join(items[1:])
        return True
                

if __name__ == '__main__':
    aicfInfo = AicfParser().parse('/home/xiaoming.zhang/ainst/ainst/test.aicf')
    print aicfInfo
