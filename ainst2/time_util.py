#! /usr/bin/python
import time
from logger import Log

def stringToSecond(value):
    '''1h 60m 3600s 3600'''
    unit = value[-1]
    result = None
    try:
        if unit == 'h':
            result = 3600 * int(value[:-1])
        elif unit == 'm':
            result = 60 * int(value[:-1])
        elif unit == 's':
            result = int(value[:-1])
        elif unit.isdigit():
            result = int(value)
    except:
        pass
    return result
        
def timeStr2Stamp(timeStr):
    #2013-
    #2013-4-
    #2013-4-21
    #2013-4-21 23:
    #2013-4-21 23:22:
    #2013-4-21 23:22:12
    if timeStr is None or timeStr == '':
        return None
    _year = '0'
    _month = '1'
    _day = '1'
    _hour = '00'
    _min = '00'
    _second = '00'
    ymdStr = None
    hmsStr = None
    items = timeStr.split()
    if len(items) == 1:
        ymdStr = timeStr
    elif len(items) == 2:
        ymdStr = items[0]
        hmsStr = items[1]
    else:
        return None
    
    if ymdStr is None or ymdStr == '':
        return None
    ymdItems = ymdStr.split('-')
    ymdLen = len(ymdItems)
    if ymdLen < 2:
        return None
    elif ymdLen == 2:
        if ymdItems[0] != '':
            _year = ymdItems[0]
        if ymdItems[1] != '':
            _month = ymdItems[1]
    elif ymdLen == 3:
        if ymdItems[0] != '':
            _year = ymdItems[0]
        if ymdItems[1] != '':
            _month = ymdItems[1]
        if ymdItems[2] != '':
            _day = ymdItems[2]
    else:
        return None

    if hmsStr is not None and hmsStr != '':
        hmsItems = hmsStr.split(':')
        hmsLen = len(hmsItems)
        if hmsLen < 2:
            return None
        elif hmsLen == 2:
            if hmsItems[0] != '':
                _hour = hmsItems[0]
            if hmsItems[1] != '':
                _min = hmsItems[1]
        elif hmsLen == 3:
            if hmsItems[0] != '':
                _hour = hmsItems[0]
            if hmsItems[1] != '':
                _min = hmsItems[1]
            if hmsItems[2] != '':
                _second = hmsItems[2]
        else:
            return None

    timeStr = "%s-%s-%s %s:%s:%s" % (_year, _month, _day, _hour, _min, _second)
    timeStamp = None
    try:
        timeStamp = time.mktime(time.strptime(timeStr, "%Y-%m-%d %H:%M:%S"))
    except:
        Log.cout(Log.ERROR, 'Time format illegal')
        return None
    return int(timeStamp)

if __name__ == "__main__":
    print stringToSecond("2h")
    print stringToSecond("2m")
    print stringToSecond("133s")
    print stringToSecond("133")
    print stringToSecond("1s3")

    print timeStr2Stamp('222a2-2-22 23:')
