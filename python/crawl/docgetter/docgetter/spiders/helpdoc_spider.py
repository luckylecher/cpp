from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item

class MySpider(CrawlSpider):
        name = 'opensearch'
        allowed_domains = ['docs.aliyun.com/']
        start_urls = ['http://docs.aliyun.com/?spm=5176.2020520121.103.8.I77IIg&tag=tun#/pub/opensearch/menu/menu']

        rules = (
                # Extract links matching 'category.php' (but not matching 'subsection.php')
                # and follow links from them (since no callback means follow=True by default).
                Rule(SgmlLinkExtractor(allow='http://docs.aliyun.com/?spm=5176.2020520121.103.8.I77IIg&tag=tun#/pub/opensearch/.*', )), callback='parse_item'),
                )

        def parse_item(self, response):
                self.log('url:%s' % response.url)
                hxs = HtmlXPathSelector(response)
                item = Item()
                item['title'] = hxs.select('//*[@id="doc-menu"]/dl/div/dd/a/span').extract
                item['url'] = response.url
                item['content'] = "test"
                return item
