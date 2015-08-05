# -*- coding: utf-8 -*-
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
        str = str.rstrip()
        if start < 0 :
            return ""
        return (str[start+7:-2]).replace(" 测试"," '测试'")

    def removeServiceIdInFilter(self, query):
        pattern = re.compile(r"\(service_id=.*?\)")
        
        if len(re.findall(re.compile(r"\(service_id=.*?\) AND"), query)) > 0:
            pattern = re.compile(r"\(service_id=.*?\) AND ")
        query = pattern.sub("",query)    
        query = query.replace("filter=&&","")
        
        pattern = re.compile(r"range\((.*?),\"\[([0-9]),([0-9])\]\"\)")
        temp = re.findall(pattern, query)
        if len(temp) < 1:
            return query
        temp =  "%s >= %s AND %s <= %s" % (temp[0][0], temp[0][1],temp[0][0],temp[0][2])
        return pattern.sub(temp,query)

    def removeHeadAndTailQuoteOfQuery(self, query):
        m = query.find("&&query=")
        if m < 0:
            return query
        m += 8
        size = len(query)-2
        quote = 0
        needRemoveQuote = False
        while m < size:
            if query[m] == "(":
                quote += 1
            elif query[m] == ")":
                quote -= 1
                if quote == 0:
                    if query[m] == "&" and query[m+1] == "&":
                        needRemoveQuote = True
                    break
            m += 1
        if needRemoveQuote:
            pattern = re.compile(r"query=\((.*?)\)&&")
            temp = re.findall(pattern, query)
            return pattern.sub("query=%s&&" % temp[0], query)
        else:
            return query

    #只针对99141的文档
    def specialQuery(self, query):
        pattern = re.compile(r"query=(.*?)&&")
        temp = re.findall(pattern, query)
        temp = temp[0].split("AND")
        newQuery = ""
        flag = True
        for item in temp:
            if item.find("|") > 0:
                newQuery += " AND (%s)" % item
                flag = False
            else:
                newQuery += " AND %s" % item
        if flag:
            return query
        newQuery = newQuery[4:]
        #pattern = re.compile(r"query=.*?&&")
        #print newQuery
        return pattern.sub("query=%s&&" % newQuery, query).replace("AND NOT","ANDNOT")

def test(x):
    fh = FormatHa3()
    fpath = "data/109556"
    f = open(fpath)
    wf = open("query4test.109556.v1.txt","a")
    doit = Doit()
    doit.setIndexList(x)
    i = 0
    flist = []
    for line in f:
        print "=========================%d======================" % i
        wf.write(line+"\n")
        line = fh.extractQuery(line)
        query = fh.removeFormula(line)
        query = fh.removeSummary(query)
        query = fh.replaceFormatValue(query)
        wf.write(str(i)+":\n"+"os:"+query + "\n")
        #生成DSL
        query = fh.removeServiceIdInFilter(query)
        #query = fh.removeHeadAndTailQuoteOfQuery(query)
        if fpath.find("99141") > 0:
            query = fh.specialQuery(query)
        wf.write("es:"+doit.deal_api(query) + "\n")
        i += 1
        #if i >= 5:
            #break
    print flist
    
def beta(x, fpath, outpath):
    fh = FormatHa3()
    f = open(fpath)
    wf = open(outpath,"w")
    ff = open(outpath+".failed","w")
    doit = Doit()
    doit.setIndexList(x)
    i = 0
    flist = []
    for line in f:
        try:
            #print "=========================%d======================" % i
            #wf.write(line + "\n")
            query = fh.extractQuery(line)
            query = fh.removeFormula(query)
            query = fh.removeSummary(query)
            query = fh.replaceFormatValue(query)
            wf.write(str(i)+":\n"+"OS.all:"+query + "\n")
            temp = query.split("&&")
            for item in temp:
                if(item.startswith("config")):
                    wf.write("OS.config:"+item+"\n")
                elif(item.startswith("query")):
                    wf.write("OS.query:"+item+"\n")
                elif(item.startswith("sort")):
                    wf.write("OS.sort:"+item+"\n")
                elif(item.startswith("filter")):
                    wf.write("OS.filter:"+item+"\n")
        #生成DSL
            query = fh.removeServiceIdInFilter(query)
            query = fh.removeHeadAndTailQuoteOfQuery(query)
            if fpath.find("99141") > 0:
                query = fh.specialQuery(query)
            wf.write("ES.all:"+doit.deal_api(query) + "\n")
            temp = doit.get_obj_by_function()
            wf.write("ES.query:"+temp['query']+"\n")
            wf.write("ES.sort:"+temp['sort']+"\n")
            wf.write("ES.filter:"+temp['filter']+"\n")
            wf.write("ES.config:"+temp['config']+"\n")
            #if i > 500:
                #break
        except Exception:
            wf.write( "failed!\n")
            ff.write(line+"\n")
            flist.append(i)
            i += 1
            continue
        i += 1
        
    print "failed:"
    print flist
    wf.close()
    f.close()

if "__main__" == __name__:
    ilist =  ["outer_id","key1","key2","key3","key4","key5","key6","key7","key8","key18","tags","mall_shop_floor","brand_name_filter","telno","activity_ids"]
    turnOn = True
    fpath = "data/99141.log"
    #fpath = "data/109556"
    outpath = "query4test.99141.v6.txt"
    #outpath = "query4test.109556.v1.txt"
    if turnOn:
        beta(ilist, fpath, outpath)
    else:
        test(ilist)
        
