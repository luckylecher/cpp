#! /usr/bin/python

import re

class HostExpander:
    def __init__(self):
        self.pattern = re.compile(r'(\[\S+?\]|\{\S+?\})')

    def expand(self, host):
        if not host:
            return None
        match = self.pattern.split(host)
        if not match:
            return []
        result = map(self._mapFunc, match)
        return reduce(self._reduceFunc, result)

    def _mapFunc(self, string):
        resultList = []
        if not string:
            resultList.append(string)
            return resultList
        if string[0] == '[' and string[-1] == ']':
            return self._mapBracket(string[1:-1])
        elif string[0] == '{' and string[-1] == '}':
            return self._mapBrace(string[1:-1])
        else:
            resultList.append(string)
        return resultList

    def _mapBrace(self, string):
        resultList = []
        numStrList = string.split(',')
        for numStr in numStrList:
            resultList.append(numStr)
        return resultList

    def _mapBracket(self, string):
        resultList = []
        numStrList = string.split(',')
        for numStr in numStrList:
            index = string.find('-')
            if index == -1:
                resultList.append(numStr)
            else:
                low = self._getIntValue(numStr[:index])
                high = self._getIntValue(numStr[index+1:])
                if low is None or high is None or high < low:
                    resultList.append('['+numStr+']')
                    continue
                while low <= high:
                    resultList.append(str(low))
                    low += 1
        return resultList

    def _reduceFunc(self, itemList1, itemList2):
        resultList = []
        for item1 in itemList1:
            for item2 in itemList2:
                resultList.append(item1+item2)
        return resultList

    def _getIntValue(self, string):
        try:
            return int(string)
        except Exception, e:
            return None
