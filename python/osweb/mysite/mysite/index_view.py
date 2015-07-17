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

        os = OpenSearch()
        kw = request.GET.get('keywords').encode('utf-8')
        if kw == "":
                return HttpResponse("empty keywords!")
        f = open("log.txt","a")
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+":"+kw+"\n")
        f.close()
        res = os.getSearchResult(kw)
        f = open("mysite/result.html")
        t = template.Template(f.read())
        c = template.Context({"keyword":kw,"all_result":res})
        return HttpResponse(t.render(c))
