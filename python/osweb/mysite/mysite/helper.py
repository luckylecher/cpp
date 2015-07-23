#encoding:utf-8
import datetime
def save_search_log(kw, page):
    f = open("log.txt","a")
    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+":"+kw+"(page:"+str(page)+")\n")
    f.close()

def get_page(page):
    if page is None:
        page = 1
    page = int(page)
    if page < 1:
        page = 1
    return page
