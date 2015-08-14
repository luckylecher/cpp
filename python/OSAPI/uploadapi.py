#encoding:utf-8
import time,re,datetime,json
import urllib,urllib2
import commands
from opensearchapi import OpenSearchAPI
class UploadAPI(OpenSearchAPI):
    def __init__(self, ak = None, secret = None, host = None):
        OpenSearchAPI.__init__(self)
        if ak is None or secret is None:
            self.setAccessKeyAndSecret("M2plnqGUH5lC4UWQ","CUJSetgXfjdEzP2tE9ZRN74BvS2Te0")
        if host is None or host == "":
            self.setHost("opensearch-cn-corp.aliyuncs.com")
        self.table_name = "main"
        self.setParam({
            "action" : "push",
            "sign_mode" : "1",
            "table_name" : self.table_name
            })
        self.setMethodToPost()

    def setTableName(self, name):
        self.table_name = name

    def uploadDoc(self, doc, id = "Unknown"):
        doc = "[%s]" % doc
        body = urllib.urlencode({"items":doc.encode("utf-8")})
        status_ok = self._sendRequest(body, id)
        time.sleep(0.3)
        return status_ok

    def _sendRequest(self, body, id):
        req = urllib2.Request(self._generateUploadURL(), body)
        response = urllib2.urlopen(req)
        res_content = json.loads(response.read())
        status_ok = False
        if "status" in res_content and res_content['status'] == "OK":
            print "Upload doc [%s] success." % id
            status_ok = True
        else:
            print res_content
            print "Upload doc [%s] failed." % id
        return status_ok

    def uploadJsonDoc(self, json_doc, id="Unknown"):
        #print json_doc
        body = json.dumps([json_doc])
        body = "items=" + urllib.quote(body)
        status_ok = self._sendRequest(body,id)
        time.sleep(0.3)
        return status_ok
    
    def _generateUploadURL(self):
        raw_url, sign = self.signature()
        raw_url = "http://%s/index/doc/%s?%s&Signature=%s" % (self.host, self.appName, raw_url, sign)
        return raw_url


if "__main__" == __name__:
    ua = UploadAPI()
    print ua.uploadDoc('[{"fields":{"id":"helloword","groupid":"2","title":"中国好声音"},"cmd":"ADD"}]', "1")
    print ua.uploadJsonDoc([{"fields":{"id":"ehome","groupid":"34","title":"china 佳偶"},"cmd":"ADD"}])
