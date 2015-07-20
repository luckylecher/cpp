#encoding:utf-8
import time,re,datetime,urllib2,json,sys,urllib
import hmac
import hashlib
import base64
from urllib import quote
class OpenSearch:
    def __init__(self):
        self.ak = "M2plnqGUH5lC4UWQ"
        self.secret = "CUJSetgXfjdEzP2tE9ZRN74BvS2Te0"
        self.appName = "OpensearchHelpDoc"
        self.suggestName = "all"
        self.host = "opensearch-cn-corp.aliyuncs.com"
        self.param = {}
        self.initQueryParam()

    def getUTC(self):
        now = datetime.datetime.utcnow().isoformat()
        return re.sub(re.compile("\..*"), "Z", now)

    def getSignatureNonce(self):
        return str(int(time.time() * 10000000))

    def initQueryParam(self):
        self.param = {
            "AccessKeyId":self.ak,
            "SignatureMethod":"HMAC-SHA1",
            "SignatureNonce":"",
            "SignatureVersion":"1.0",
            "Timestamp":"",
            "Version":"v2",
            "query":"",
            "index_name":self.appName
            }
        self.order = sorted(self.param.iteritems(), key=lambda d:d[0])

    def generateQueryParam(self,keyword, start, hit):
        self.param['SignatureNonce'] = self.getSignatureNonce()
        self.param['Timestamp'] = self.getUTC()
        self.param['query'] = "query=content:'"+keyword+"'&&config=start:"+str(start)+",hit:"+str(hit)

    def encode(self, str):
        return quote(str).replace("%7E", "~")
    
    def generateURL(self):
        raw_url = ""
        for item in self.order:
            raw_url += item[0] + "=" + self.encode(self.param[item[0]]) + "&"
        raw_url = raw_url[:len(raw_url) - 1]
        signature = self.encode(self.caculateHMAC(raw_url))
        raw_url = "http://" + self.host + "/search?"+raw_url+"&Signature="+signature.replace("/","%2F")
        #return "/search?"+raw_url+"&Signature="+signature.replace("/","%2F")
        return raw_url

    def caculateHMAC(self, str):
        str = "GET&%2F&" + self.encode(str);
        secret = self.secret + "&"
        return base64.b64encode(
            hmac.new(secret,str,digestmod=hashlib.sha1).digest()
            )

    def sendRequest(self, path):
        conn = httplib.HTTPConnection(self.host)

        conn.request("GET", path)
        r1 = conn.getresponse()
        result = r1.read()
        if r1.status != 200:
            print "respond:" + str(r1.status)
            return
        conn.close()
        return result

    def getSearchResult(self, key, start, hit):
        #key = urllib.unquote(str(key)).decode('utf8')
        self.generateQueryParam(key, start, hit)
        url =  self.generateURL()
        response = urllib2.urlopen(url)
        html = response.read()
        res_obj = json.loads(html)
        if res_obj['status'] != "OK":
            print "search result not ok!"
            return None
        else:
            return res_obj['result']
    
    def test(self):
        self.generateQueryParam("Hello")
        url =  self.generateURL()
        response = urllib2.urlopen(url)
        html = response.read()
        res_obj = json.loads(html)
        for res in res_obj['result']['items']:
            print res['content']

#OpenSearch().test()
