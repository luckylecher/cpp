#coding:utf-8
import hashlib,sys
from uploader import OpenSearch
import codecs
from urllib import urlencode
import urllib
import json
class MakeJsonFile:
    def __init__(self):
        self.fpath = ""
        self.outpath = ""
        self.log_file = "docs/upload_logs.txt"
        self.log_obj = None

    def beginUpload(self):
        f = codecs.open(self.fpath,encoding="UTF-8")
        uploader = OpenSearch()
        id = statu = counter = 0
        title = content = ""
        all = ""
        for line in f:
            #print type(line)
            if statu == 0:
                if line.startswith("id="):
                    id = line.rstrip()[3:]
                    statu = 1
            elif statu == 1:
                if line.startswith("title="):
                    title = line.rstrip()[6:]
                    statu = 2
            elif statu == 2:
                if line.startswith("content="):
                    content = line[8:]
                    statu = 3
                else:
                    title += line
            elif statu == 3:
                if line.startswith("link="):
                    link = line.rstrip()[5:]
                    link_hash = self._getHash(link.split("/").pop())
                    content_hash = self._getHash(content)
                    if self.log_obj.has_key(link_hash) and content_hash == self.log_obj[link_hash]:
                        print "%s doc not change, not upload!" % id
                    else:
                        self.log_obj[link_hash] = content_hash
                        temp = self.generateItem(id,title,content,link,link_hash)
                        uploader.uploadDoc("items=" + urllib.quote(("["+temp[:-1]+"]").encode("utf8")), id)
                    counter += 1
                    statu = 0
                else:
                    content += line
        print "有%d条数据被处理了" % counter
        f.close()

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

    def generateItem(self, id, title, content, link, link_hash, navi="OpenSearch"):
        template = '{"fields":{"id":"%s","title":"%s","content":"%s","link":"%s","md5":"%s"},"cmd":"ADD"},'
        return template  % (id, title, content
                            .replace("\\u","\\ u")
                            .replace("\\","\\\\")
                            .replace("\\x", "\\ x")
                            .replace("\"","\\\"")
                            .replace("\t","    ")
                            .replace("\n","\\n"),
                            link,link_hash)

if __name__ == "__main__":
    mjf = MakeJsonFile()
    fname = "html.final.txt"#sys.argv[1]
    mjf.setPath(fname)
    mjf.deal()
