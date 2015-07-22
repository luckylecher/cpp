from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item
from docgetter.items import DocgetterItem
from scrapy.spider import Spider

class MySpider(CrawlSpider):
        name = 'opensearch'
        allowed_domains = ['docs.aliyun.com','wwww.baidu.com']
        start_urls = ['http://docs.aliyun.com/#/pub/opensearch']

        rules = (
                Rule(LinkExtractor(allow='.*', ),callback = 'parse_item'),
        )

        def parse_item(self, response):
                print response.url
                self.log('url:%s' % response.url)
                items = []
                hxs = HtmlXPathSelector(response)
                item = DocgetterItem()
                item['title'] = hxs.select('//*[@id="doc-menu"]/dl/div/dd/a/span').extract()
                item['url'] = str(response.url)
                item['content'] = "test"
                items.append(item)
                items.append(make_requests_from_url("http://www.baidu.com"))
                return items
