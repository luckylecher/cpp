#coding:utf-8
from opensearchapi import OpenSearchAPI
import json
class SearchAPI(OpenSearchAPI):
    def __init__(self):
        OpenSearchAPI.__init__(self)
        self.appName="HDoc_V8"
        self.setParam({'query':'','index_name':''})
        self.setHost("opensearch-cn-corp.aliyuncs.com")
        self.requestNum = 0

    def search(self, keyword, start, hit, web_tag = 'tun'):
        keyword = keyword.replace("\\","\\\\")
        self.requestNum += 1
        self.param['query'] = "query=default:'"+keyword+"' AND (tag:'all' OR tag:'"+web_tag+"')&&config=start:"+str(start)+",hit:"+str(hit)
        self.param['index_name'] = self.appName
        req, sign = self.signature()
        url = "http://%s/search?%s&Signature=%s" % (self.host, req, sign)
        return self._formatResult(self.request(url))

    def _formatResult(self, result_str):
        if result_str is None:
            return None
        result_obj = None
        try:
            result_obj = json.loads(result_str)
        except Exception,e:
            print "Convert into json failed!"
            return None
        if result_obj['status'] != "OK":
            print result_obj['errors']
            return None
        return result_obj['result']
