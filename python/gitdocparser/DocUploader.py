#coding:utf-8
import hashlib,sys
import codecs
from urllib import urlencode
import urllib
import json
import re
import sys
import os
sys.path.append("/Users/licheng/Documents/git/cpp/python/OSAPI/")
import uploadapi
DEBUG = False
class OpenSearchDocUploader:
    def __init__(self, appName, ak, secret, host, navigateMap = None):
        self.fpath = ""
        self.outpath = ""
        self.log_file = "upload_logs.txt"
        self.log_obj = None
        if navigateMap is None:
            self.category = {
                "brief-manual":1,
                "quick-start":2,
                "api-reference":3,
                "sdk":4,
                "best-practice":5
            }
        else:
            self.category = navigateMap
        self.count = 0
        self._readLog()
        self.uploader = uploadapi.UploadAPI(ak, secret, host)
        self.uploader.setAppName(appName)

    def setNavigationMapping(self, dict):
        self.category = dict

    def getID(self, link):
        if DEBUG:
            return self.count
        try:
            cat_key = re.compile(r"(.*?)/").findall(link)[0]
        except Exception,e:
            return -1
        if cat_key not in self.category:
            return -1
        self.count += 1
        return self.category[cat_key] * 1000 + self.count

    def uploadDoc(self, docObj):
        id = self.getID(docObj['link_suffix'])
        if id < 0:
            print "doc not in config, jump!"
            return
        link_hash = self._getHash(docObj['link_suffix'])
        content_hash = self._getHash(docObj['content'])
        if self.log_obj.has_key(link_hash) and content_hash == self.log_obj[link_hash]:
            print "%s doc not change, not upload!" % id
        else:
            docObj['md5'] = link_hash
            docObj['id'] = str(id)
            temp = self.generateItem(id, docObj)
            if DEBUG:
                self.f.write(temp.encode("utf-8"))
            res = self.uploader.uploadDoc(temp, id)
            if res:
                self.log_obj[link_hash] = content_hash
        self._updateLog()

    def _getHash(self, str):
        m = hashlib.md5()
        m.update(str.encode("utf8"))
        return m.hexdigest()

    def _readLog(self):
        f = None
        try:
            f = codecs.open(self.log_file)
            self.log_obj = json.load(f)
        except Exception,e:
            #self.log_obj = {}
            print "Log file dose not exist, create it!"
            open(self.log_file, "w").write("{}")
        finally:
            if self.log_obj is None:
                self.log_obj = {}
            if f is not None:
                f.close()

    def _updateLog(self):
        f = codecs.open(self.log_file, "w")
        json.dump(self.log_obj, f)
        f.close()

    def setLogFile(self, log):
        self.log_file = log

    def generateItem(self, id, docObj):
        item_content = u'{"fields":%s,"cmd":"ADD"}' % json.dumps(docObj)
        #print item_content
        return item_content
