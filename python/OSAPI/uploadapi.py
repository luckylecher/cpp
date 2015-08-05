#encoding:utf-8
import time,re,datetime,urllib2,json,httplib
import hmac
import hashlib
import base64
from urllib import quote
import commands
from opensearchapi import OpenSearchAPI
class UploaderAPI(OpenSearchAPI):
    def __init__(self):
        OpenSearchAPI.__init__(self)
        self.setAccessKeyAndSecret("M2plnqGUH5lC4UWQ","CUJSetgXfjdEzP2tE9ZRN74BvS2Te0")
        self.appName = "HDoc_V2" 
        self.setHost("opensearch-cn-corp.aliyuncs.com")
        self.table_name = "main"
        self.setParam({
            "action" : "push",
            "sign_mode" : "1",
            "table_name" : self.table_name
            })
        self.setMethodToPost()

    def uploadDocNotEncoded(self, doc, id):
        pass
    
    def uploadDoc(self, doc, id):
        
        print "upload doc: %s " % id
        cmd =  '''curl -POST '%s' -d '%s' ''' % (self.generateUploadURL(), doc)
        #print cmd
        cmd_status, http_result = commands.getstatusoutput(cmd)
        #print cmd_status, http_result
        if http_result.find('"status":"OK"') > 0:
            pass #print "Success!"
        else:
            print "Failed:%s" % http_result
        time.sleep(0.3)
        return cmd
    
    def generateUploadURL(self):
        raw_url, sign = self.signature()
        raw_url = "http://%s/index/doc/%s?%s&Signature=%s" % (self.host, self.appName, raw_url, sign))
        return raw_url

    def sendDoc(self, url, body):
        conn = httplib.HTTPConnection(self.host)
        conn.request("POST", url, body)
        r1 = conn.getresponse()
        result = r1.read()
        print result
