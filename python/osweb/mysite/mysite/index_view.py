#encoding:utf-8
from django.http import HttpResponse
from django import template
from opensearch import OpenSearch
import urllib
import helper

def hello(request):
        f = open("mysite/index.html")
        return HttpResponse(f)

def search(request):
        hit = 15 #每页结果数
        os = OpenSearch()
        kw = request.GET.get('keywords').encode('utf-8')
        if kw == "":
                return HttpResponse("关键字不能为空!<a href=\"../index\">返回</a>")
        page = helper.get_page( request.GET.get('page') )
        start = (page - 1) * hit
        helper.save_search_log(kw, page)
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
        for item in res['items']:
                item['id'] = int(item['id'])
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
def my_custom_error_view(request):
        return HttpResponse("<H1>错误!</H1>")
