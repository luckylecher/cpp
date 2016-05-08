#! /usr/bin/python
import os
from logger import Log
import file_util

class SettingStreamer:
    def __init__(self):
        pass

    def dump(self, settingMap, destPath):
        if settingMap is None:
            return False
        content = ''
        for key, value in settingMap.iteritems():
            content += str(key) + '=' + str(value) + '\n'
        return file_util.writeToFile(destPath, content)

    def parse(self, path):
        if not file_util.exists(path):
            Log.cout(Log.DEBUG, 'Path [%s] not exists' % path)
            return {}
        content = file_util.readFromFile(path)
        if content is None:
            Log.cout(Log.ERROR, 'Read setting file [%s] failed' % path)
            return None
        lines = content.split('\n')
        settingMap = {}
        for line in lines:
            if line.strip() == '':
                continue
            pos = line.find('=')
            if pos == -1:
                Log.cout(Log.ERROR, 'Setting file [%s ]illega' % path)
                return None
            key = line[0:pos]
            value = line[pos+1:]
            settingMap[key] = value
        return settingMap


if __name__ == '__main__':
    settingWrapper = SettingWrapper()
    print settingWrapper.parse('./agg.settings')
    from aicf import *
    aicfInfo = AicfParser().parse('/home/xiaoming.zhang/ainst/ainst/agg.aicf')
    print settingWrapper.merge('./agg.settings', aicfInfo.settings, False)
