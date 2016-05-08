#-coding:utf-8
import re
from conversion import Doit
class FormatHa3:
    def __init__(self):
        pass

    def removeSummary(self, query):
        return query.replace("no_summary:yes,","")

    def removeFormula(self, query):
        #非贪心匹配，取出kvpair
        pattern = re.compile(r",first_formula.*?&&")
        return pattern.sub("&&",query)

    def replaceFormatValue(self, query):
        return query.replace("format:protobuf","format:xml")

    def extractQuery(self, str):
        start = str.find("query=[")
        if start < 0 :
            return ""
        return str[start+7:-2]

    def removeServiceIdInFilter(self, query):
        pattern = re.compile(r"\(service_id=.*?\)")
        query = pattern.sub("",query)
        return query.replace("filter=&&","")

    def removeHeadAndTailQuoteOfQuery(self, query):
        pattern = re.compile(r"query=\((.*?)\)&&")
        res = re.findall(pattern,query)
        if len(res) == 0:
            return query
        return pattern.sub("query=%s&&" % res[0], query)
        

if "__main__" == __name__:
    fh = FormatHa3()
    f = open("testdata.txt")
    wf = open("outputdata.txt","a")
    doit = Doit()
    for line in f:
        line = fh.extractQuery(line)
        query = fh.removeFormula(line)
        query = fh.removeSummary(query)
        query = fh.replaceFormatValue(query)
        print "before:\n%s\nafter:\n%s" % (line, query)
        wf.write("os:"+query + "\n")
        #生成DSL
        query = fh.removeServiceIdInFilter(query)
        query = fh.removeHeadAndTailQuoteOfQuery(query)
        wf.write("es:"+doit.deal_api(query) + "\n")
        wf.flush()
    wf.close()
    f.close()
        
