# -*- coding: utf-8 -*-
import re
import simplejson as json
class FilterTerm:
    CONJUNCTION = 0 #ANDOR
    LQUOTE = 1
    RQUOTE = 2
    OPERATOR = 3
    EXPRESSION = 4
    FUNCTION = 4
    WORD = 5
    CACULATE = 6
    exp = ['in','notin','fieldlen','in_polygon','in_query_polygon']
    ops = ['>','<','>=','<=','!=','=']
    cacu = ['+','-','*','/','&','^','|']

class Doit:
    def __init__(self):
        self.index_list = []
        self.location_name = {
            "posx":"location",
            "real_posx":"real_location"
            }
        self.all_obj = {}
    def setIndexList(self, ilist):
        self.index_list = ilist

    def deal_api(self, str):
        #print "Deal String [ %s ]" % str
        self.all_obj = {}
        all_clause = str.split("&&")
        config_clause = query_clause = sort_clause = filter_clause = None
        for item in all_clause:
            str = item.lstrip()
            #query开头
            if str.startswith("query"):
                query_clause = str[str.find('=')+1:]
            elif str.startswith("sort"):
                sort_clause = str[str.find('=')+1:]
            elif str.startswith("filter"):
                filter_clause = str[str.find('=')+1:]
            elif str.startswith("config"):
                config_clause = str[str.find('=')+1:]
            else:
                pass
                #print "ignore clause: [%s]" % str

        if(query_clause.lstrip().rstrip() == "''" or query_clause.lstrip().rstrip() == ''):
            #print json.dumps({"match_all":{}})#查询所有结果
            query_obj = {"match_all":{}}
        else:
            query_obj = self.generate_es_query(0, self.get_query_clause_item( query_clause ))
            self.all_obj['query'] = json.dumps(query_obj)

        search_str = ""            
        if filter_clause is not None:
            filter_obj,k = self.generate_es_filter_obj(0, self.get_filter_clause_terms( filter_clause ))
            self.all_obj['filter'] = json.dumps(filter_obj)
            search_str += '"query": {"filtered": {    "query":'+ json.dumps(query_obj) +',    "filter": '+json.dumps(filter_obj)+'}}'
        elif filter_clause is None:
            search_str += '"query":'+json.dumps(query_obj)
            self.all_obj['filter'] = ""

        if sort_clause is not None:
            sort_str = self.sort_json(sort_clause)
            search_str=sort_str+','+search_str
            self.all_obj['sort'] = sort_str
        else:
            self.all_obj['sort'] = ""

        if config_clause is not None:
            config_str = self.get_config_clause(config_clause)
            search_str = config_str + search_str
            self.all_obj['config'] = config_str
        else:
            self.all_obj['config'] = ""

        search_str = "{" + search_str + "}"
            
        #print search_str
        return search_str

    def get_obj_by_function(self):
        return self.all_obj

    def get_config_clause(self, str):
        start_pattern = re.compile(r"start:([0-9]*)")
        hit_pattern = re.compile(r"hit:([0-9]*)")
        rank_pattern = re.compile(r"rank_size:([0-9]*)")
        start_value = re.findall(start_pattern, str)
        hit_value = re.findall(hit_pattern, str)
        rank_value = re.findall(rank_pattern, str)
        if( len(start_value) <= 0 ):
            start_value = 0
        else:
            start_value = int(start_value[0])
        if( len(hit_value) <= 0 ):
            hit_value = -1
        else:
            hit_value = int(hit_value[0])
        if len(rank_value) > 0:
            rank_value = int(rank_value[0])
        else:
            rank_value = -1
        config_string = ('"from":%d,' % start_value)
        if(hit_value >= 0):
            config_string += ('"size":%d,' % hit_value)
        if(rank_value >= 0):
            config_string += ('"terminate_after":%d,' % rank_value)
        return config_string
        
            
    def append(self, str):
        if str != '':
            self.strs.append(str)

    def is_query_char(self, char):
        return (char >= 'A' and char <= 'z') or char == "'" or char == '"' or char == ':' or (char >= '0' and char <= '9') or char == '^' or char == '_' or char == '.' or char == '-'
    

    def get_query_clause_item(self, query):
        str = ""
        self.strs = []
        flag = False
        isFirstOr = True
        for char in query:
            if flag:#现在进入的是关键字内部，直到读到另一个引号才退出
                if char == "'" or char == '"':
                    str += char
                    self.append(str)
                    str = ""
                    flag = False
                else:
                    str += char
            elif char == "'" or char == '"':
                flag = True #后面的内容是关键字
                str += char
            elif char == "|":
                self.append(str)
                self.append("OR")
                str = str.split(":")
                str = str[0]+":"
            elif char == '(' or char == ')':
                self.append(str)
                str = ""
                self.strs.append(char)
            elif char == ' ':
                self.append(str)
                str = ""
            elif self.is_query_char(char):
                str += char
            else:
                str += char
        if str != "":
            self.strs.append(str)
        #print self.strs
        return self.strs

    #判断index的类型是否是string
    def index_is_string(self, idx):
        return idx in self.index_list

    def generate_es_query_segment(self, os_segment):
        if os_segment.find(':') < 0:
            return {"query_string":{"query":"default:"+os_segment}}
        elif self.index_is_string(os_segment[: os_segment.find(':')]):
            return {"term":{os_segment[: os_segment.find(':')]:{"value":os_segment[os_segment.find(':') + 1:].replace("'","").replace('"',"")}}}
        return {"query_string":{"query":os_segment.replace("'","").replace('"','\"')}}

    def generate_es_query(self, start, qterm):
        statu = 0
        must = []
        should = []
        must_not = []
        prestatu = 0
        i = start
        start = len(qterm)
        kw = None
        while i < start:
            if statu == 6 :
                #状态转移
                if qterm[i] == 'AND':
                    statu = prestatu = 1
                elif qterm[i] == 'ANDNOT':
                    statu = prestatu = 2
                elif qterm[i] == 'RANK':
                    statu = prestatu = 3
                elif qterm[i] == '(':
                    #进入到括号里面处理
                    res,i = self.generate_es_query(i+1, qterm)
                    if prestatu == 1 or prestatu == 0:
                        must.append(res)
                    elif prestatu == 2:
                        must_not.append(res)
                    elif prestatu == 3:
                        should.append(res)
                elif qterm[i] == ')':
                    #刚刚结束一个语句，该返回bool表达式了
                    return {"bool":{"must":must,"must_not":must_not,"should":should}}, i
                elif qterm[i] == 'OR':
                    statu = prestatu = 4
                else:
                    print qterm
                    float("error")
            elif statu >0 :
                #如果后面跟的是括号,则直接跳出去处理括号
                if qterm[i] == '(':
                    statu = 6
                    continue
                temp = self.generate_es_query_segment(qterm[i])
                if statu == 1:
                    must.append(temp)
                elif statu == 2:
                    must_not.append(temp)
                elif statu == 3 or statu == 4:
                    should.append(temp)
                statu = 6
            elif statu == 0:
                #初始状态,只是处理第一个表达式,处理完转到状态6,开始后面的处理
                #开始的(要特殊处理
                if qterm[i] == '(':
                    temp,i = self.generate_es_query(i+1, qterm)#直接处理括号内部内容,返回bool
                else:
                    temp = self.generate_es_query_segment(qterm[i])
                j = i + 1
                #根据表达式后面的一个term确定temp放入哪个区域
                if j >= start:
                    must.append(temp)
                elif qterm[j] == 'OR':
                    should.append(temp)
                else:
                    must.append(temp)
                statu = 6
            i += 1
        return {"bool":{"must":must,"must_not":must_not,"should":should}}

    def type_of_filter_term(self, term):
        if term == 'AND' or term == 'OR':
            return FilterTerm.CONJUNCTION
        elif term == '(':
            return FilterTerm.LQUOTE
        elif term == ')':
            return FilterTerm.RQUOTE
        elif term in FilterTerm.ops:
            return FilterTerm.OPERATOR
        elif term in FilterTerm.exp:
            return FilterTerm.EXPRESSION
        elif term in FilterTerm.cacu:
            return FilterTerm.CACULATE
        else:
            return FilterTerm.WORD

    def get_distance_string_in_filter(self, start, strs):
        size = len(strs)
        if start + 9> size:
            print "bad distance function"
            print strs
            float("error")
            return None,-1
        fieldName = self.location_name[strs[start+2]]
        return {"geo_distance":{"ditance":strs[start+8],fieldName+".location":{"lat":float(strs[start+4].replace('"',"")),"lon":float(strs[start+5].replace('"',''))}}},start + 8
        
    #处理过滤表达式,支持函数,返回最后一个元素的位置
    def analyze_filter_expression(self, start, fterms):
        size = len(fterms)
        #距离函数
        if fterms[start] == "distance":
            return self.get_distance_string_in_filter(start, fterms)
        if start + 2 >= size:
            print "expression error : at fterms[%d]" % start
            print fterms
            float("error")
            return None, -1
            
        elif self.type_of_filter_term(fterms[start]) != FilterTerm.WORD:
            print "expression start wrong: at fterms[%d]" % start
            print fterms
            float("error")
            return None, -1
        field_name = fterms[start]
        start += 1
        if self.type_of_filter_term(fterms[start]) == FilterTerm.OPERATOR:
            if self.type_of_filter_term(fterms[start+1]) == FilterTerm.WORD:
                return self.generate_es_range_segment(fterms[start], fterms[start -1], fterms[start + 1]), start +1
            else:
                print "expression end wrong: [%s %s %s]" % (fterms[start -1], fterms[start], fterms[start +1])
                print fterms
                float("error")
                return None,-1
        else:
            print "expression wrong: [%s %s %s]" % (fterms[start -1], fterms[start], fterms[start +1])
            print start,fterms
            float("error")
            return None,-1

    def generate_es_function_obj(self, start, fterms):
        size = len(fterms)
        #未完待续...

    def is_digit(self, numstr):
        isInt = True
        try:
            int(numstr)
        except ValueError:
            isInt = False
        try:
            float(numstr)
        except ValueError:
            return isInt
        return True

    def generate_es_range_segment(self, opt, fieldName, value):
        if opt == '>':
            return {"range":{fieldName:{"gt":value.replace("\"","")}}}
        elif opt == '<':
            return {"range":{fieldName:{"lt":value.replace("\"","")}}}
        elif opt == '>=':
            return {"range":{fieldName:{"gte":value.replace("\"","")}}}
        elif opt == '<=':
            return {"range":{fieldName:{"lte":value.replace("\"","")}}}
        elif opt == '=':
            return {"term":{fieldName:value.replace("\"","")}}
        elif opt == '!=':
            return {"not":{"filter":{"term":{fieldName:value.replace("\"","")}}}}
        else:
            print "generate es range obj error"
            float("error")
            return None

    def get_filter_clause_terms(self, str):
        self.strs = []
        size = len(str)
        term = ""
        i = 0
        while i < size:
            if str[i] == '-' and str[i+1] >= '0' and str[i+1]<='9':
                self.append(term)
                term = '-'
            elif str[i] == "(" or str[i] == ")" or str[i] == "=" or (str[i] in FilterTerm.cacu):
                self.append(term)
                term = ""
                self.strs.append(str[i])
            elif str[i] == " " or str[i] == ',':
                self.append(term)
                term = ""
            elif str[i] == '>' or str[i] == '<' or str[i] =='!':
                self.append(term)
                term = str[i]
                if str[i+1] == '=':
                    self.append(term + '=')
                    term = ""
                    i += 1
                else:
                    self.append(term)
                    term = ""
            elif self.is_query_char(str[i]):
                term += str[i]
            else:
                print "get filter clause terms wrong"
                print str
                float("error")
            i += 1
        self.append(term)
        #print self.strs
        return self.strs

    def generate_es_filter_obj(self, start, fterms):
        statu = 0
        i = start
        must=[]
        pre = 2
        should = []
        while i < len(fterms):
            type = self.type_of_filter_term(fterms[i])
            if statu == 0:
                #分析当前段的属性,是算数表达式还是布尔表达式,返回最后一个term的位置
                res_tag,seg_tail = self.pattern_analyze(i,fterms)
                if res_tag == "c":
                    #生成script脚本
                    temp = self.generate_es_script_obj(i,seg_tail,fterms)
                    i = seg_tail
                elif type == FilterTerm.LQUOTE:
                    #左括号,而且内部不是算数表达式,递归调用
                    temp, i = self.generate_es_filter_obj(i + 1, fterms)
                elif res_tag == "o" and type != FilterTerm.LQUOTE:
                    #分析表达式,返回最后一个term所在的位置
                    temp, i = self.analyze_filter_expression(i,fterms)
                else:
                    print "wrong"
                    print fterms
                    float("error")
                    return
                if i+1 < len(fterms):
                    if fterms[i+1] == "OR":
                        should.append(temp)
                    else:
                        must.append(temp)
                else:
                    must.append(temp)
                statu = 1
            elif statu == 1:
                if fterms[i] == "AND":
                    pre = 2
                elif fterms[i] == "OR":
                    pre = 3
                elif fterms[i] == ")":
                    return {"bool":{"must":must,"should":should}}, i
                else:
                    #分析当前段的属性,是算数表达式还是布尔表达式,返回最后一个term的位置
                    res_tag,seg_tail = self.pattern_analyze(i,fterms)
                    if res_tag == "c":
                        #生成script脚本
                        temp = self.generate_es_script_obj(start,seg_tail,fterms)
                        i = seg_tail
                    elif res_tag == "o" and type != FilterTerm.LQUOTE:
                        #分析表达式,返回最后一个term所在的位置
                        temp, i = self.analyze_filter_expression(i,fterms)
                    elif type == FilterTerm.LQUOTE:
                        #左括号,而且内部不是算数表达式,递归调用
                        temp, i = self.generate_es_filter_obj(i + 1, fterms)
                    else:
                        print "wrong"
                        print fterms
                        float("error")
                        return
                    if pre == 2:
                        must.append(temp)
                    elif pre == 3:
                        should.append(temp)
            i += 1
        return {"bool":{"must":must,"should":should}},0

    def generate_es_script_obj(self, head, tail, fterms):
        script_str = ""
        while head <= tail:
            type = self.type_of_filter_term(fterms[head])
            if type  == FilterTerm.WORD and not self.is_digit(fterms[head]):
                script_str += "doc['"+fterms[head] +"'].value"
            else:
                script_str += fterms[head]
            head += 1
        return {"script":{"script":script_str}}

    def pattern_analyze(self, start, fterms):
        statu=0
        quote = 0
        while start < len(fterms):
            type = self.type_of_filter_term(fterms[start])
            if statu == 0:
                if type == FilterTerm.CACULATE:
                    statu = 1
                elif type == FilterTerm.OPERATOR:
                    statu = 2
                elif type == FilterTerm.LQUOTE:
                    quote += 1
                elif fterms[start] == "distance":
                    statu = 2
            #直接读取到下一个连接符
            elif statu == 1:
                if type == FilterTerm.CONJUNCTION:
                    if quote > 0:
                        return "o",start -1
                    return "c", start - 1#需要使用script
                elif type == FilterTerm.LQUOTE:
                    quote += 1
                elif type == FilterTerm.RQUOTE:
                    quote -= 1
                elif start == len(fterms) - 1:
                    return "c", start
            elif statu == 2:
                return "o", start - 1#需要使用range或者其它函数
            elif statu == 3:
                if type == FilterTerm.LQUOTE:
                    return "d",start - 1
                else:
                    return "o",start - 1
            start += 1
        print "pattern validate failed"
        print fterms
        float("error")
        return "error2", -1
    
    def sort_json(self, sortstr):
        para=''
        sortstr = sortstr.replace(' ','')
        str_list = sortstr.split(';')
        for x in str_list:
            str_temp = x[1:len(x)]
            if str_temp == 'RANK':
                str_temp = '_sorce'
            sort_style = ''
            if x[0]=='+':
                sort_style = 'asc'
            elif x[0]=='-':
                sort_style = 'desc'
            if str_temp[0:9] == 'distance(':
                str2 = str_temp[9:-1].split(',')
                para += '{"_geo_distance":{"'+self.location_name[str2[0]]+'.location":"'+str2[2].replace('"','')+','+str2[3].replace('"','')+'","order":"'+sort_style+'"},'
                continue
            para +='{"'+str_temp+'":"'+sort_style+'"},'
        ans = '"sort":['
        ans += para[0:len(para)-1]+']'
        return ans



if __name__ == "__main__":
    doit = Doit()
    doit.deal_api('config=hit:1,format:xml,qrs_chain:search,inner_result_compress:z_speed_compress,rank_size:1000000,sourceid:984369793,kvpairs:app_name#store_relation&&query=biz_type:"100" AND outer_id:"20195187613"&&filter=(service_id=99141) AND (status>=0 AND check_status>=0 AND distance(posx,posy,"0.0","0.0")<=40.0)&&sort=+distance(posx,posy,"0.0","0.0")&&cluster=general&&kvpairs=app_name:99141,request_id:143783937817452807827674,schema_version:1437034175&&layer=range:service_id{99141},quota:UNLIMITED&&searcher_cache=use:yes,expire_time:now()+300')
    doit.deal_api('query=(belong:"68167372" OR belong_parents:"68167372") AND biz_type:"100" ANDNOT "测试"&&filter=(((check_status >=0 OR check_status = -6)) AND ((outer_tags=61762 OR outer_tags=61826)) AND (type =3) AND outer_tags=60610 AND ((status=1 OR status=0)) AND (key16>=1437753600000 AND key16<=1437839384874 AND key17>=1437839384874 AND key17<=1437839999874))')
    #temp = doit.get_filter_clause_terms('')
    #print "===result==="
    #ans,k = doit.generate_es_filter_obj(0,temp)
    ##print ans
    #print '{  "query": {"filtered": {    "query": {      "match_all": {}    },    "filter": '+json.dumps(ans)+'}}}'
