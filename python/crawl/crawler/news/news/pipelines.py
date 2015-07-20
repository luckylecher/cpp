# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import codecs
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi
from hashlib import md5

class NewsPipeline(object):
    def __init__(self):
        self.file = codecs.open('sinanews.json', 'wb', encoding='utf-8')
        
    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + '\n'
        self.file.write(line.decode('unicode_escape'))
        return item

class MySQLStoreNewsPipeline(object):
    def __init__(self):
        self.dbpool = adbapi.ConnectionPool('MySQLdb',
            host = 'rdspvrpty4cq5ov1ysxon.mysql.rds.aliyuncs.com',
            db = 'database1',
            user = 'admin1',
            passwd = 'admin1',
            cursorclass = MySQLdb.cursors.DictCursor,
            charset = 'utf8',
            use_unicode = True
        )

    #pipeline默认调用
    def process_item(self, item, spider):
        d = self.dbpool.runInteraction(self._do_insert, item, spider)
        d.addErrback(self._handle_error, item, spider)
        return item
    
    #将每行更新或写入数据库中
    def _do_insert(self, conn, item, spider):
        urlmd5id = self._get_urlmd5id(item)
        conn.execute('select * from news where id = %s', (urlmd5id, ))
        ret = conn.fetchone()
        if ret:
            pass
        else:
            conn.execute('insert into news(id, title, content, public_time, category, source, url) values(%s, %s, %s, %s, %s, %s, %s)', \
                         (urlmd5id, item['title'], item['content'], item['public_time'], item['category'], item['source'], item['url']))

    #获取url的md5编码
    def _get_urlmd5id(self, item):
        #text进行md5处理，为避免重复采集设计
        return md5(item['url']).hexdigest()
    
    #异常处理
    def _handle_error(self, failure, item, spider):
        log.err(failure)
