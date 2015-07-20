#encoding:utf-8
from django.http import HttpResponse
from django import template
from opensearch import OpenSearch
import datetime
import urllib

def hello(request):
        f = open("mysite/index.html")
        return HttpResponse(f)

def search(request):
        hit = 15 #每页结果数
        os = OpenSearch()
        kw = request.GET.get('keywords').encode('utf-8')
        if kw == "":
                return HttpResponse("empty keywords!")
        page = request.GET.get('page')
        if page is None:
                page = 1
        page = int(page)
        if page < 1:
                page = 1
        start = (page - 1) * hit
        f = open("log.txt","a")
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+":"+kw+"\n")
        f.close()
        res = os.getSearchResult(kw, start, hit)
        if res is None:
                return HttpResponse("内部错误,请联系 砺诚")
        num = res['num']
        nextPage = page + 1
        if not (res['total'] > page * hit):
                nextPage = 0
        prePage = page -1
        f = open("mysite/result.html")
        t = template.Template(f.read())
        c = template.Context({
                "keyword":kw,
                "all_result":res['items'],
                "total":res['total'],
                "num":res['num'],
                "searchtime":res['searchtime'],
                "page":page,
                "nextPage":nextPage,
                "prePage":prePage
                })
        return HttpResponse(t.render(c))
