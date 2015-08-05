from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy import log
from docgetter.items import DocgetterItem

class TestSpider(Spider):
    name = "test"
    allowed_domains = ["w3school.com.cn"]
    start_urls = [
        "http://www.w3school.com.cn/xml/xml_syntax.asp"
        ]
    def parse(self, response):
        sel = Selector(response)
        sites = sel.xpath('//div[@id="navsecond"]/div[@id="course"]/ul[1]/li')
        items = []
        for site in sites:
            item = DocgetterItem()
            item['title'] = "1"
            item['content'] = "2"
            item["url"] = "3"
            items.append(item)
        return items
