#! /usr/bin/python

import urllib2
import socket
from logger import Log
import file_util

class FetchError:
    FETCH_SUCCESS = 0
    FETCH_TIMEOUT = 1
    FETCH_TOO_LARGE = 2
    FETCH_OTHER_ERROR = 3

    @staticmethod
    def getErrorString(code):
        if code == FetchError.FETCH_SUCCESS:
            return 'success'
        elif code == FetchError.FETCH_TIMEOUT:
            return 'timeout'
        elif code == FetchError.FETCH_TOO_LARGE:
            return 'too large'
        elif code == FetchError.FETCH_OTHER_ERROR:
            return 'other error'
        return 'unkown'
        
class FileFetcher:
    def __init__(self, timeout=5, tryTimes=3, maxFileLength=1024*1024*1024*2):
        self.timeout = timeout
        self.tryTimes = tryTimes
        self.maxFileLength = maxFileLength
        self.lineLength = 1024 * 1024

    def _isChunked(self, response):
        transferEncoding = response.info().getheader('Transfer-Encoding')
        if transferEncoding and transferEncoding.lower() == 'chunked':
            return True
        return False

    def _doFetch(self, url):
        socket.setdefaulttimeout(self.timeout)
        try:
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            chunked = self._isChunked(response)
            content = ''
            if not chunked:
                length = int(response.info().getheader('Content-Length'))
                if length > self.maxFileLength:
                    return FetchError.FETCH_TOO_LARGE, None
                content = response.read()
            else:
                length = 0
                while True:
                    line = response.readline(self.lineLength)
                    if not line:
                        break
                    content += line
                    length += len(line)
                    if length > self.maxFileLength:
                        return FetchError.FETCH_TOO_LARGE, None
            response.close()
            return FetchError.FETCH_SUCCESS, content
        except Exception, e:
            Log.cout(Log.ERROR, 'Fetch failed: %s' % e)
            if hasattr(e, 'reason'):
                if str(e.reason) == 'timed out':
                    return FetchError.FETCH_TIMEOUT, None
            return FetchError.FETCH_OTHER_ERROR, None
        
    def fetch(self, srcUrl, destFile):
        content = ''
        for i in range(self.tryTimes):
            ret, content = self._doFetch(srcUrl)
            if ret != FetchError.FETCH_TIMEOUT:
                break
        if ret != FetchError.FETCH_SUCCESS:
            err = FetchError.getErrorString(ret)
            Log.cout(Log.ERROR, 'Fetch [%s] failed: %s' % (srcUrl, err))
            return False
        return file_util.writeToFile(destFile, content)

if __name__ == '__main__':
    print FileFetcher().fetch('http://wenwen.soso.com/z/q396111756.htm?ch=wtk.title', './test.tmp')
    print FileFetcher().fetch('http://10.250.8.21/repos/release/5Server/x86_64/AliWS-data-1.3.0.4-1.el5.4.x86_64.rpm', './test.tmp')
