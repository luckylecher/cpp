import sys
import simplejson as json

import httplib
import urllib
from threadpool import *
class EsApi:
    es_param = {
        'es_addr':'10.125.224.80',
        'es_port':'9200',
        'es_search_dir':None,
        'es_bulk_dir':None,
        'es_index':None,
        'es_type':None
        }
    es_schema = {}

    def entrance(self,fpath):
        self.parseData(fpath,0)

    def setParam(self,param):
        self.es_param = param

    def assignSpecifiedParam(self,key,value):
        if key in self.es_param:
            self.es_param[key] = value
        else:
            print "Invalid key!"

    def setEsSchema(self,new_schema):
        self.es_schema = new_schema

    def request(self,method = 'POST',dir_path='',data=None):
        httpClient = None
        try:
            httpClient = httplib.HTTPConnection(self.es_param['es_addr'], self.es_param['es_port'])
            if data is None:
                httpClient.request(method, dir_path)
            else:
                httpClient.request(method, dir_path,data)
            response = httpClient.getresponse()
            if int(response.status) != 201:
                print 'post %d error:%s' %(index_id, str(response))
                print "body:\n%s" % response.read()
                return False
            else:
                return True
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()
                return False

    def sendSingleData(self,index_id,json_data):
        httpClient = None
        try:
            httpClient = httplib.HTTPConnection(self.es_param['es_addr'], self.es_param['es_port'])
            httpClient.request("POST", 
                               '/'+self.es_param['es_index']+'/'+self.es_param['es_type']+'/'+str(index_id), 
                               json_data)
            response = httpClient.getresponse()
            if int(response.status) != 201:
                print 'post %d error:%s' %(index_id, str(response))
                return False
            else:
                return True
        except Exception, e:
            print e
        finally:
            if httpClient:
                httpClient.close()
                return False
    
    def createIndex(self,index_name):
        self.request(method = 'POST',dir_path = '/'+index_name+'?pretty')

    def parseData(self,fpath,start):
        fp = open(fpath, 'r')
        print "Begin to work with %s" % fpath
        doc_data = []
        json_datas = []
        ids = []
        i = 0
        pk = None
        counter = 0;
        for line in fp:
            if line == '\x1e\n':
                pk,json_doc = self.parseOneDoc(doc_data)
                if pk is None:
                    doc_data = []
                    i = i + 1
                    continue

                if(i >= start):
                    self.sendSingleData(pk,json_doc)
                doc_data = []
                i = i + 1
            else:
                doc_data.append(line)
        print "%s doc number is : %d" % (fpath,i)
        fp.close()


    def parseOneDoc(self,raw_data):
        content = {}
        data_count = len(raw_data)
        if data_count == 0:
            return None
        i = 0
        pk = None
        while i < data_count:
            field_value = raw_data[i].split('=')
            if len(field_value) < 2:
                i = i + 1
                continue
            field = field_value[0]
            value = field_value[1]
            if not value.endswith('\x1f\n'):
                while i + 1 < data_count:
                    i = i + 1
                    if raw_data[i].endswith('\x1f\n'):
                        break
            i = i + 1
            if field == 'pk':
                pk = value[:-2]
            if field in self.es_schema:
                if value.endswith('\x1f\n'):
                    value = value[:-2]
                if len(value) == 0:
                    continue
                if 'int' == self.es_schema[field]:
                    content[field] = int(value)
                else:
                    content[field] = value
        return pk,json.JSONEncoder().encode(content)

def multi_worker(new_schema):
    thread_pool = ThreadPool(32, 1000)
    boss = EsApi()
    boss.setEsSchema(new_schema)
    boss.assignSpecifiedParam('es_index','test5')
    boss.assignSpecifiedParam('es_type','main')

    for i in range(0,257):
        fp = '/home/lecher.lc/es/110794/part-%05d' % i
        reqs = makeRequests(boss.entrance, [fp]);
        [thread_pool.putRequest(req) for req in reqs] 
    thread_pool.wait() 

    
if '__main__' == __name__:
    new_schema = {
        'body': 'string', 
        'cat_id': 'int', 
        'm_image_location': 'string', 
        'm_image_height': 'int', 
        'id': 'int', 
        'brand_s': 'string', 
        'user_id': 'int', 
        'geo_id_4_i': 'int', 
        'title': 'string', 
        'cat_id_3_i': 'int', 
        'file_location': 'string', 
        'image_width': 'int', 
        'modelnumber': 'string', 
        'source': 'int', 
        'state': 'int', 
        'image_height': 'int', 
        'reason': 'int', 
        'productid': 'string', 
        'type': 'int', 
        'brand': 'int', 
        'cat_id_1_i': 'int', 
        'status': 'int', 
        'image_location': 'string', 
        'price': 'int', 
        'm_image_width': 'int', 
        'specialty': 'int', 
        'postfrom': 'int', 
        'cat_id_4_i': 'int', 
        'phone_s': 'string', 
        'geo_id_3_i': 'int', 
        'geo_id_5_i': 'int', 
        'small_body': 'string', 
        'modified_datetime': 'int', 
        'geo_id_2_i': 'int', 
        'game': 'int', 
        'geo_id': 'int', 
        'total_img': 'int', 
        'cat_id_2_i': 'int'
        }        
    multi_worker(new_schema)
