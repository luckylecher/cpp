#-coding:utf-8
import sys,httplib,urllib
import json

class Validata:
    def __init__(self):
        self.port = 9200
    def setHost(self, ip):
        self.ip = ip
    def setPort(self, port):
        self.port = port
    def setIndexName(self, name):
        self.index_name = name
    def setTypeName(self, type):
        self.type_name = type
    def validateQuery(self, query):
        httpClient = None
        try:
            httpClient = httplib.HTTPConnection(self.ip, self.port)
            httpClient.request("GET",
                               '/'+self.index_name+'/_validate/query', 
                               query)
            response = httpClient.getresponse()
            print response.status
            if int(response.status) == 200:
                res_obj = json.loads(str(response.read()))
                return res_obj['validate']
            else:
                return int(response.status)
        except Exception, e:
            print e
            return e
        finally:
            if httpClient:
                httpClient.close()

if "__main__" == __name__:
    v = Validata()
    v.setHost("10.125.224.80")
    v.setPort(9200)
    v.setIndexName("query")
    v.setTypeName("test")
    print v.validateQuery("{'a'}")
