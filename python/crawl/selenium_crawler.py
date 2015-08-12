#coding:utf-8
from selenium import webdriver
import re
import traceback
import time
import codecs
class SCrawler:
    def __init__(self):
        self.start = "https://docs.aliyun.com/#/tun/opensearch/menu/menu-internal"
        self.domain = "https://docs.aliyun.com/"
        self.urls = []
        self.ff = None
        self.url_ptn = re.compile(r'href="(#/tun/opensearch/.*?)"')
        self.file = "html.txt"

    def get_all_url(self):
        driver = self.ff
        driver.get(self.start)
        ele = driver.find_element_by_css_selector("#doc-api-1218 > div > div > div > div.doc-span10.help-content")
        html = ele.get_attribute("innerHTML")
        print html
        hrefs = re.findall(self.url_ptn, html)
        print len(hrefs)
        for item in hrefs:
            self.urls.append(self.domain + item.replace("&amp;","&"))
        print self.urls

        f = codecs.open(self.file, "w",encoding="utf-8", errors="ignore")
        fail_list = []
        for item in self.urls:
            if len(item.split("/")) < 8:
                continue
            print "deal %s" % item
            driver.get(item)
            time.sleep(3)
            ele = None
            try:
                ele = driver.find_element_by_css_selector("#doc")
            except Exception,e:
                traceback.print_exc()
                fail_list.append(item)
                continue
            f.write("yhb~\n"+ele.get_attribute("innerHTML")+"\nlink="+item+"\n")
        print fail_list
        f.close()

    def start_crawler(self, file="html.txt"):
        try:
            self.file = file
            self.ff = webdriver.Firefox()
            self.get_all_url()
        except Exception,e:
            traceback.print_exc()
        finally:
            self.ff.close()

if "__main__" == __name__:
    sc = SCrawler()
    sc.start_crawler()
