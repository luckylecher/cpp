#encoding:utf-8
import datetime,sys
def save_search_log(kw, page):
    print >> sys.stderr,"_oslog_ [query info @" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] <query='" + kw + "'> with <page=" + str(page) + ">\n"
    return None
    f = open("/home/lecher.lc/weblog/log.txt","a")
    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+":"+kw+"(page:"+str(page)+")\n")
    f.close()

def save_search_result_info(kw, total):
    print >> sys.stderr,"_oslog_ [search result @ %s] <query='%s'> with <result='%d'>" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kw, total)

def get_page(page):
    if page is None:
        page = 1
    page = int(page)
    if page < 1:
        page = 1
    return page
