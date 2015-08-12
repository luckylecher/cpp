#coding:utf-8
import time,re,datetime,urllib2,json,sys,urllib
import hmac
import hashlib
import base64
from urllib import quote
import httplib
class OpenSearchAPI:
    def __init__(self):
        self.ak = "M2plnqGUH5lC4UWQ"
        self.secret = "CUJSetgXfjdEzP2tE9ZRN74BvS2Te0"
        self.host = "opensearch-cn-corp.aliyuncs.com"
        self.method = "GET"
        self.param = {}
        self.appName = ""

    def setAppName(self, name):
        self.appName = name

    def setAccessKeyAndSecret(self, ak, sc):
        self.ak = ak
        self.secret = sc

    def setHost(self, host):
        self.host = host

    def getUTC(self):
        now = datetime.datetime.utcnow().isoformat()
        return re.sub(re.compile("\..*"), "Z", now)

    def getSignatureNonce(self):
        return str(int(time.time() * 10000000))

    def setParam(self, param):
        self.param = param
        self.param['SignatureNonce'] = ""
        self.param['Timestamp'] = ""
        self.param['AccessKeyId'] = self.ak
        self.param['SignatureMethod'] = "HMAC-SHA1"
        self.param['SignatureVersion'] = "1.0"
        self.param['Version'] = "v2"
        self._sortParam()

    def _sortParam(self):
        self.order = sorted(self.param.iteritems(), key=lambda d:d[0])

    def addParam(self, key, value):
        self.param[key] = value
        self._sortParam()

    def encode(self, str):
        return quote(str).replace("%7E", "~").replace("/","%2F")

    def signature(self):
        self.param['SignatureNonce'] = self.getSignatureNonce()
        self.param['Timestamp'] = self.getUTC()
        raw_url = ""
        for item in self.order:
            raw_url += item[0] + "=" + self.encode(self.param[item[0]]) + "&"
        raw_url = raw_url[:len(raw_url) - 1]
        signature = self.encode(self.caculateHMAC(raw_url))
        return raw_url, signature

    def setMethodToGet(self):
        self.method = "GET"

    def setMethodToPost(self):
        self.method = "POST"

    def caculateHMAC(self, str):
        str = self.method + "&%2F&" + self.encode(str);
        secret = self.secret + "&"
        return base64.b64encode(
            hmac.new(secret,str,digestmod=hashlib.sha1).digest()
            )

    def request(self, path, body = None):
        conn = httplib.HTTPConnection(self.host)
        if body is None:
            conn.request(self.method, path)
        else:
            conn.request(self.method, path, body)
        r1 = conn.getresponse()
        result = r1.read()
        if r1.status != 200:
            print "status is not 200 [%s]" % str(r1.status)
            return None
        conn.close()
        return result

