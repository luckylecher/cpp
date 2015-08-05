#encoding:utf-8
import time,re,datetime,urllib2,json,httplib
import hmac
import hashlib
import base64
from urllib import quote
import commands
class OpenSearch:
    def __init__(self):
        self.ak = "M2plnqGUH5lC4UWQ"
        self.secret = "CUJSetgXfjdEzP2tE9ZRN74BvS2Te0"
        self.appName = "HDoc_V2" #"HDoc"
        self.suggestName = "all"
        self.host = "opensearch-cn-corp.aliyuncs.com"
        self.param = {}
        self.table_name = "main"

    def getUTC(self):
        now = datetime.datetime.utcnow().isoformat()
        return re.sub(re.compile("\..*"), "Z", now)

    def getSignatureNonce(self):
        return str(int(time.time() * 10000000))

    def setParam(self, param = {}):
        self.param = param
        self.param["AccessKeyId"] = self.ak
        self.param["SignatureMethod"] = "HMAC-SHA1"
        self.param["SignatureVersion"] = "1.0"
        self.param["SignatureNonce"] = self.getSignatureNonce()
        self.param["Timestamp"] = self.getUTC()
        self.param["Version"] = "v2"
        self.order = sorted(param.iteritems(), key = lambda d:d[0])

    #url = "http://%s/index/doc/%s?" % (self.host, self.appName)

    def uploadDoc(self, doc, id):
        self.generateUploadParam()
        url = self.generateUploadURL()
        print "upload doc: %s " % id
        cmd =  '''curl -POST 'http://%s%s' -d '%s' ''' % (self.host, url, doc)
        #print cmd
        cmd_status, http_result = commands.getstatusoutput(cmd)
        #print cmd_status, http_result
        if http_result.find('"status":"OK"') > 0:
            pass #print "Success!"
        else:
            print "Failed:%s" % http_result
        time.sleep(0.3)
        return cmd

    def generateUploadParam(self):
        param = {
            "action" : "push",
            "sign_mode" : "1",
            "table_name" : self.table_name
        }
        self.setParam(param)

    def encode(self, str):
        return quote(str).replace("%7E", "~")
    
    def generateUploadURL(self):
        raw_url = ""
        for item in self.order:
            raw_url += item[0] + "=" + self.encode(self.param[item[0]]) + "&"
        raw_url = raw_url[:-1]
        signature = self.encode(self.caculateHMAC(raw_url))
        raw_url = "/index/doc/%s?%s&Signature=%s" % (self.appName, raw_url, signature.replace("/","%2F"))
        #return "/search?"+raw_url+"&Signature="+signature.replace("/","%2F")
        return raw_url

    def caculateHMAC(self, str):
        str = "POST&%2F&" + self.encode(str);
        secret = self.secret + "&"
        return base64.b64encode(
            hmac.new(secret,str,digestmod=hashlib.sha1).digest()
            )

    def sendDoc(self, url, body):
        conn = httplib.HTTPConnection(self.host)
        conn.request("POST", url, body)
        r1 = conn.getresponse()
        result = r1.read()
        print result

    def test(self):
        self.generateQueryParam("Hello")
        url =  self.generateURL()
        response = urllib2.urlopen(url)
        html = response.read()
        res_obj = json.loads(html)
        for res in res_obj['result']['items']:
            print res['content']

#OpenSearch().test()
