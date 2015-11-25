#coding:utf-8
from opensearchapi import OpenSearchAPI
import json
class SuggestAPI(OpenSearchAPI):
    def __init__(self, app_name, suggest_name):
        OpenSearchAPI.__init__(self)
        self.appName= app_name
        self.suggestName = suggest_name
        self.setParam({'query':'','index_name':'','hit':'','suggest_name':''})
        self.setHost("opensearch-cn-corp.aliyuncs.com")

    def getSuggest(self, query, hit):
        self.param['query'] = query
        self.param['index_name'] = self.appName
        self.param['hit'] = str(hit)
        self.param['suggest_name'] = self.suggestName
        req, sign = self.signature()
        url = "http://%s/suggest?%s&Signature=%s" % (self.host, req, sign)
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
        if "errors" in result_obj:
            print result_obj['errors']
            return None
        return result_obj['suggestions']

    def setSuggestName(self, name):
        self.suggestName = name

if "__main__" == __name__:
    sa = SuggestAPI()
    sa.setSuggestName("all")
    suggestions = sa.getSuggest("s", 10)
    for item in suggestions:
        print item['suggestion']
    
