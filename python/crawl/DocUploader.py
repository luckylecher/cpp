#coding:utf-8
import hashlib,sys
from uploader import OpenSearch
import codecs
from urllib import urlencode
import urllib
import json
import re
import sys
sys.path.append("/Users/licheng/Documents/git/cpp/python/OSAPI/")
import uploadapi
class OpenSearchDocUploader:
    def __init__(self):
        self.fpath = ""
        self.outpath = ""
        self.log_file = "docs/upload_logs.txt"
        self.log_obj = None
        self.category = {
            "brief-manual":1,
            "quick-start":2,
            "api-reference":3,
            "sdk":4,
            "best-practice":5,
            "menu":6
        }
        self.count = 0
        self._readLog()
        self.uploader = uploadapi.UploadAPI()
        self.uploader.setAppName("HDoc_V5")
        self.f = codecs.open("docs/final1.txt", "w", "utf-8")

    def uploadDocFromFile(self):
        f = codecs.open(self.fpath,encoding="UTF-8")
        uploader = OpenSearch()
        id = statu = counter = 0
        title = content = ""
        all = ""
        for line in f:
            #print type(line)
            if statu == 0:
                if line.startswith("doc_id="):
                    id = line.rstrip()[7:]
                    statu = 1
            elif statu == 1:
                if line.startswith("doc_title="):
                    title = line.rstrip()[10:]
                    statu = 2
            elif statu == 2:
                if line.startswith("doc_content="):
                    content = line[12:]
                    statu = 3
                else:
                    title += line
            elif statu == 3:
                if line.startswith("doc_link="):
                    link = line.rstrip()[9:]
                    link_hash = self._getHash(link.split("/").pop())
                    content_hash = self._getHash(content)
                    if self.log_obj.has_key(link_hash) and content_hash == self.log_obj[link_hash]:
                        print "%s doc not change, not upload!" % id
                    else:
                        temp = self.generateItem(id,title,content,link,link_hash)
                        print temp
                        if uploader.uploadDoc("items=" + urllib.quote(("["+temp[:-1]+"]").encode("utf8")), id):
                            self.log_obj[link_hash] = content_hash
                        else:
                            print temp
                    counter += 1
                    statu = 0
                else:
                    content += line
        print "有%d条数据被处理了" % counter
        f.close()

    def getID(self, link):
        self.count += 1
        return self.category[re.findall(re.compile(r"opensearch\/(.*?)/"), link)[0]] * 1000 + self.count

    def uploadDoc(self, docObj):
        id = self.getID(docObj['link'])
        link_hash = self._getHash(docObj['link'].split("/").pop())
        content_hash = self._getHash(docObj['content'])
        if self.log_obj.has_key(link_hash) and content_hash == self.log_obj[link_hash]:
            print "%s doc not change, not upload!" % id
        else:
            docObj['md5'] = link_hash
            docObj['id'] = id
            temp = self.generateItem(id, docObj)
            res = self.uploader.uploadDoc(temp[:-1], id)
            if res:
                self.log_obj[link_hash] = content_hash
            else:
                print temp
        self._updateLog()

    def entrancy(self):
        self._readLog()
        self.beginUpload()
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
            print "file not exist"
        finally:
            if self.log_obj is None:
                self.log_obj = {}
            if f is not None:
                f.close()

    def _updateLog(self):
        f = codecs.open(self.log_file, "w")
        json.dump(self.log_obj, f)
        f.close()
                    
    def setPath(self, path):
        self.fpath = path
        self.outpath = path[:-4] + ".forOS.txt"

    def setLogFile(self, log):
        self.log_file = log

    def generateItem(self, id, docObj):
        template = '{"fields":%s,"cmd":"ADD"},'
        return template  % json.dumps(docObj)
               #(abstract.replace("\r\n","  ").replace("\n",""), id, title, content
                            #.replace("\\u","\\ u")
                            #.replace("\\","\\\\")
                            #.replace("\\x", "\\ x")
                            #.replace("\"","\\\"")
                            #.replace("\t","    ")
                            #.replace("\r\n","  ").replace("\n","  "),
                            #link,link_hash)
