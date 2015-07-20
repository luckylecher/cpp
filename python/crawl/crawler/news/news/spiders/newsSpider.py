# -*- coding=utf8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from news.items import NewsItem

class NewsSpider(CrawlSpider):
    name = 'sinanews'
    allowed_domains=['sina.com.cn']
    start_urls = []
    #for i in xrange(310, 0, -1):
        #start_urls.append('http://roll.news.sina.com.cn/s/channel.php?ch=01#col=89&spec=&type=&ch=01&k=&offset_page=0&offset_num=0&num=60&asc=&page=' + str(i))
    #start_urls = ['http://roll.news.sina.com.cn/s/channel.php?ch=01#col=89&spec=&type=&date=2015-06-01&ch=01&k=&offset_page=0&offset_num=0&num=10000&asc=&page=1']
    start_urls = ['http://roll.news.sina.com.cn/interface/rollnews_ch_out_interface.php?col=89&spec=&type=&ch=01&k=&offset_page=0&offset_num=0&num=80&asc=&page=233']
    
    rules = [Rule(LinkExtractor(allow = '/.+/.*\d+.s?html', deny = '/.+/v/.+/\d+.s?html'), 'parse_news'),
             Rule(LinkExtractor(restrict_xpaths = u"//a[@title='下一页']"), callback = 'parse_next')]

    def parse_news(self, response):
        news = NewsItem()

        news['url'] = response.url

        temp = response.xpath("//h1[@id='artibodyTitle']//text()").extract()
        news['title'] = temp[0] if temp else ''

        temp = response.xpath("//span[@id='media_name']//a//text()").extract()
        news['source'] = temp[0] if temp else ''
        if news['source'] == '':
            temp = response.xpath("//span[@data-sudaclick='media_name']//a//text()").extract()
            news['source'] = temp[0] if temp else ''

        temp =  response.xpath("//span[@id='pub_date']//text()").extract()
        news['public_time'] = temp[0] if temp else ''
        if news['public_time'] == '':
            temp =  response.xpath("//span[@class='time-source']//text()").extract()
            news['public_time'] = temp[0] if temp else ''
        if news['public_time'] != '':
            news['public_time'] = self.get_datetime(news['public_time'])

        temp = response.xpath("//div[@id='artibody']//p//text()").extract()
        news['content'] = '\n'.join(temp) if temp else ''

        cat = response.url.split('//')[1].split('.')[0]
        sub_cat = response.url.split('//')[1].split('/')[1]
        news['category'] = self.get_category(cat, sub_cat)

        return news

    def parse_next(self, response):
        return self.make_requests_from_url(response.url)

    def get_datetime(self, datetime):
        datetime = datetime.encode('utf8').strip()
        elems = datetime.split('年')
        YY = elems[0]
        elems = elems[1].split('月')
        MM = elems[0]
        elems = elems[1].split('日')
        dd = elems[0]
        elems = elems[1].split(':')
        hh = elems[0]
        mm = elems[1]
        ss = '00'
        return YY + '-' + MM + '-' + dd + ' ' + hh + ':' + mm + ':' + ss

    def get_category(self, cat, sub_cat):
        ret = ''
        if cat == 'tech':
            if sub_cat == 'i':
                ret = '互联网'
            if sub_cat == 't':
                ret = '电信'
            if sub_cat == 'it':
                ret = 'IT'
            if sub_cat == 'mobile':
                ret = '手机'
            if sub_cat == 'digi':
                ret = '数码'
            if sub_cat == 'e':
                ret = '家电'
            else:
                ret = '科技'
        elif cat == 'mil':
            ret = '军事'
        elif cat == 'finance':
            if sub_cat == 'stock':
                ret = '股票'
            else:
                ret = '财经'
        elif cat == 'sports':
            if sub_cat == 'nba':
                ret = 'NBA'
            elif sub_cat == 'cba':
                ret = 'CBA'
            elif sub_cat == 'g':
                ret = '国际足球'
            elif sub_cat == 'china':
                ret = '国内足球'
            elif sub_cat == 'o' or sub_cat == 'others':
                ret = '综合体育'
            elif sub_cat == 't':
                ret = '网球'
            elif sub_cat == 'go':
                ret = '棋牌'
            elif sub_cat == 'golf':
                ret = '高尔夫'
            elif sub_cat == 'l':
                ret = '彩票'
            elif sub_cat == 'f1':
                ret = 'F1赛车'
            elif sub_cat == 'outdoor':
                ret = '户外'
            else:
                ret = '体育'
        elif cat == 'ent':
            if sub_cat == 'm':
                ret = '电影'
            if sub_cat == 's':
                ret = '明星'
            if sub_cat == 'v' or sub_cat == 'tv':
                ret = '电视'
            if sub_cat == 'y':
                ret = '音乐'
            if sub_cat == 'j':
                ret = '戏剧'
            else:
                ret = '娱乐'
        elif cat == 'news':
            if sub_cat == 'c':
                ret = '国内'
            elif sub_cat == 'w':
                ret = '国际'
            elif sub_cat == 's':
                ret = '社会'
            elif sub_cat == 'media':
                ret = '传媒'
            elif sub_cat == 'pl':
                ret = '评论'
            else:
                ret = '其他'
        elif cat == 'sky':
            ret = '航空'
        elif cat == 'outdoor':
            ret = '户外'
        elif cat == 'fashion':
            ret = '时尚'
        elif cat == 'eladies':
            ret = '女性'
        elif cat == 'health':
            ret = '健康'
        elif cat == 'collection':
            ret = '收藏'
        elif cat == 'games':
            ret = '游戏'
        return ret
