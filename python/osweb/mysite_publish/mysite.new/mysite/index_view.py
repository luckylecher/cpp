#encoding:utf-8
from django.http import HttpResponse
from django import template
import urllib
import helper
from searchapi import SearchAPI
from suggestapi import SuggestAPI
import json

WEB_TAG = "tun"
URL_PREFIX = "https://docs.aliyun.com/#/%s/opensearch/" % WEB_TAG
print URL_PREFIX
searcher = SearchAPI()
suggest = SuggestAPI("HDoc_V8", "aaa")
hello_page_template = "mysite/index.html"
search_page_template = "mysite/result.html"

def hello(request):
        f = open(hello_page_template)
        return HttpResponse(f)

def search(request):
        hit = 15 #每页结果数
        kw = request.GET.get('keywords').encode('utf-8')
        if kw == "":
                return HttpResponse("关键字不能为空!<a href=\"../index\">返回</a>")
        page = helper.get_page( request.GET.get('page') )
        start = (page - 1) * hit
        helper.save_search_log(kw, page)
        res = searcher.search(kw, start, hit, WEB_TAG)
        if res is None:
                return HttpResponse("内部错误,请联系 砺诚")
        num = res['num']
        nextPage = page + 1
        if not (res['total'] > page * hit):
                nextPage = 0
        prePage = page -1
        helper.save_search_result_info(kw, res['total'])
        f = open(search_page_template)
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
                "prePage":prePage,
                "urlPrefix":URL_PREFIX
                })
        return HttpResponse(t.render(c))

def my_custom_error_view(request):
        return HttpResponse("<H3>Sorry, this page is not for you~</H3>")

def get_suggest(request):
        kw = request.GET.get('keywords').encode('utf-8')
        res = suggest.getSuggest(kw, 10)
        response = {}
        tmp = []
        if res is None:
                response['status'] = "FAIL"
        else:
                response['status'] = "OK"
                for item in res:
                        tmp.append(item['suggestion'])
        response['result'] = tmp
        return HttpResponse(json.dumps(response), content_type="application/json")
