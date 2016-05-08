#! /usr/bin/python

from logger import Log
import file_util

class UnsetFileParser:
    def parse(self, fileName):
        content = file_util.readFromFile(fileName)
        if content is None:
            Log.cout(Log.ERROR, 'Read unset file [%s] failed' % fileName)
            return None

        unsetDict = {}
        lines = content.split('\n')
        for line in lines:
            line =  line.strip()
            if line == '' or line.startswith('#'):
                continue
            items = line.split('.')
            if len(items) < 2:
                continue
            pkgName = items[0]
            key = ('.').join(items[1:])
            unsetDict.setdefault(pkgName, set([])).add(key)
            
        return unsetDict
    
