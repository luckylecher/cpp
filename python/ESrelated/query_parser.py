#!/usr/bin/env python
#coding:utf-8
import sys,re
import json
class ClauseParser(object):
    def __init__(self):
        self.query_char_list = ['"',"'",':','_','.','-','+']
    
    def parse_clause(self, clause):
        clause = self.pre_treatment(clause)
        self.analyze_clause(clause)
        return self.process_clause()

    def process_clause(self):
        pass

    def pre_treatment(self, clause):
        return clause

    def analyze_clause(self, clause):
        pass

    def is_query_char(self, char):
        return char.isalnum() or char in self.query_char_list 

    def is_digit(self, numstr):
        if numstr.isdigit():
            return True
        try:
            float(numstr)
        except ValueError:
            return False
        return True

    def create_bool_obj(self, must, must_not, should):
        ans = {"bool":{}}
        if len(must) > 0:
            ans['bool']['must'] = must
        if len(must_not) > 0:
            ans['bool']['must_not'] = must_not
        if len(should) > 0:
            ans['bool']['should'] = should
        return ans

class QueryClauseParser(ClauseParser):
    def __init__(self):
        super(ClauseParser, self).__init__()
        self.strs = []
        self.index_list = []

    #预处理，将 A=a|b|c 的语句括起来
    def pre_treatment(self, clause):
        return clause

    def process_clause(self):
        return json.dumps(self.generate_es_query(0, self.strs))

    def append(self, str):
        if str != '':
            self.strs.append(str)    

    #判断index的类型是否是string
    def index_is_string(self, idx):
        return idx in self.index_list
    
    def analyze_clause(self, query):
        str = ""
        self.strs = []
        flag = None
        skipNext = False
        ptn = re.compile(r"\\")
        for char in query:
            if skipNext:
                str += char
                skipNext = False
                continue
            elif flag is not None:#现在进入的是关键字内部，直到读到另一个引号才退出
                if char == '\\':
                    skipNext = True
                    str += char
                elif (char == "'" and flag == "'") or (char == '"' and flag == "\""):
                    str += char
                    self.append(str)
                    str = ""
                    flag = None
                else:
                    str += char
            elif char == "'" or char == '"':
                flag = char #后面的内容是关键字
                str += char
            elif char == "^":
                str = self.strs.pop() + "^"
            elif char == "|":
                self.append(str)
                #找到前一项，提取key值
                str = self.strs[len(self.strs) - 1]
                self.append("SPEOR")
                str = str.split(":")
                str = str[0]+":"
            elif char == '(' or char == ')':
                self.append(str)
                str = ""
                self.strs.append(char)
            elif char == ' ':
                self.append(str)
                str = ""
            else:
                str += char
        if str != "":
            self.strs.append(str)

        self.deal_multi_or_operator()
        return self.strs

    #处理查询串中有 | 的情况，将 | 的语句使用括号括起来
    def deal_multi_or_operator(self):
        idx = 0
        head_point = -1
        while idx < len(self.strs):
            if self.strs[idx] == "SPEOR":
                head_point = idx - 1
                break
            idx += 1
        if head_point < 0:
            return
        while idx < len(self.strs):
            if self.strs[idx] == "SPEOR":
                self.strs[idx] = "OR"
                last_point = idx + 2
                idx += 2
            else:
                break
        self.strs.insert(last_point, ")")
        self.strs.insert(head_point, "(")
        self.deal_multi_or_operator()

    def generate_es_query_segment(self, os_segment):
        obj = {}
        if os_segment.find(':') < 0:
            obj['query_string'] = {}
            obj['query_string']['query'] = "default:" + os_segment
        elif self.index_is_string(os_segment[ :os_segment.find(':')]):
            obj['term'] = {}
            break_point = os_segment.find(':')
            field = os_segment[:break_point]
            raw_value = os_segment[break_point + 1:]
            obj['term'][field] = {}
            obj['term'][field]['value'] = raw_value.replace("\\'","").replace("'","").replace('"',"").replace("","'")
        else:
            obj['query_string'] = {}
            obj['query_string']['query'] = os_segment.replace("\\'","").replace("'","").replace('"','\"').replace("","'")
        return obj

    def generate_es_query(self, start, qterm):
        statu = 0
        must = []
        should = []
        must_not = []
        prestatu = 0
        i = start
        while i < len(qterm):
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
                    return self.create_bool_obj(must, must_not, should), i
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
                if j >= len(qterm):
                    must.append(temp)
                elif qterm[j] == 'OR':
                    should.append(temp)
                else:
                    must.append(temp)
                statu = 6
            i += 1
        return self.create_bool_obj(must, must_not, should)

class FilterTerm:
    CONJUNCTION = 0 #ANDOR
    LQUOTE = 1
    RQUOTE = 2
    OPERATOR = 3 #ops
    EXPRESSION = 4 #exp
    FUNCTION = 4
    WORD = 5
    CACULATE = 6
    exp = ['in','notin','fieldlen','in_polygon','in_query_polygon']
    ops = ['>','<','>=','<=','!=','=']
    cacu = ['+','-','*','/','&','^','|']


class FilterClauseParser(ClauseParser):
    def __init__(self):
        super(FilterClauseParser, self).__init__()
        self.strs = []
        self.location_name = {
            "posx":"location",
            "real_posx":"real_location"
            }

    def append(self, str):
        if str != '':
            self.strs.append(str)

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
                    if quote == 0:
                        return "c", start - 1
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
    
    def generate_es_script_obj(self, head, tail, fterms):
        script_str = ""
        while head <= tail:
            type = self.type_of_filter_term(fterms[head])
            if type  == FilterTerm.WORD \
                    and not self.is_digit(fterms[head]):
                script_str += "doc['"+fterms[head] +"'].value"
            else:
                script_str += fterms[head]
            head += 1
        return {"script":{"script":script_str}}

    def get_distance_string_in_filter(self, start, strs):
        size = len(strs)
        if start + 9 > size:
            print "bad distance function"
            print strs
            float("error")
            return None,-1
        fieldName = self.location_name[strs[start+2]]
        obj = {}
        obj['geo_distance'] = {}
        obj['geo_distance']['distance'] = float(strs[start + 8])
        obj['geo_distance']['unit'] = 'km'
        obj['geo_distance'][fieldName] = {}
        obj['geo_distance'][fieldName]['lat'] = float(strs[start + 4].replace('"',""))
        obj['geo_distance'][fieldName]['lon'] = float(strs[start + 5].replace('"',''))
        return (obj, start + 8)

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
            return (None, -1)
            
        elif self.type_of_filter_term(fterms[start]) != FilterTerm.WORD:
            print "expression start wrong: at fterms[%d]" % start
            print fterms
            float("error")
            return (None, -1)
        field_name = fterms[start]
        start += 1
        if self.type_of_filter_term(fterms[start]) == FilterTerm.OPERATOR:
            if self.type_of_filter_term(fterms[start+1]) == FilterTerm.WORD:
                temp = self.generate_es_range_segment(fterms[start], fterms[start -1], fterms[start + 1])
                return (temp, start +1)
            else:
                print "expression end wrong: [%s %s %s]" % (fterms[start -1], fterms[start], fterms[start +1])
                print fterms
                float("error")
                return (None,-1)
        else:
            print "expression wrong: [%s %s %s]" % (fterms[start -1], fterms[start], fterms[start +1])
            print start,fterms
            float("error")
            return (None,-1)

    def analyze_clause(self, str):
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

    def process_clause(self):
        res, pos = self.generate_es_filter_obj(0, self.strs)
        return json.dumps(res)


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
                    return (self.create_bool_obj(must, [], should), i)
                else:
                    #分析当前段的属性,是算数表达式还是布尔表达式,返回最后一个term的位置
                    res_tag,seg_tail = self.pattern_analyze(i,fterms)
                    if res_tag == "c":
                        #生成script脚本
                        temp = self.generate_es_script_obj(i,seg_tail,fterms)
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
        return (self.create_bool_obj(must, [], should), 0)


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



class SortClauseParser(ClauseParser):
    def __init__(self):
        super(SortClauseParser, self).__init__()
        self.clause = ""

    def pre_treatment(self, clause):
        self.clause = clause

    def process_clause(self):
        return self.sort_json(self.clause)

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
                para += '{"_geo_distance":{"'+self.location_name[str2[0]]+'":"'+str2[2].replace('"','')+','+str2[3].replace('"','')+'","order":"'+sort_style+'"}},'
                continue
            if str_temp[0] =='(':
                str1=str_temp.replace('+',',')
                str1= str1.replace('-',',')
                str1 = str1.replace('*',',')
                str1= str1.replace('/',',')
                str2 = str1[1:-1].split(',')
                para += '{"_script":{"script":"doc[\''+str2[0]+"'].value"
                i=1
                for x in str_temp:
                    if x == '+' or x=='-' or x=='*' or x=='/':
                        para += x + "doc['"+str2[i]+"'].value"
                        i +=1
                para += '","order":"'+sort_style+'"}},'
                continue
            para +='{"'+str_temp+'":"'+sort_style+'"},'
        ans = '"sort":['
        ans +=para[0:len(para)-1]+']'
        return ans

class AggClauseParser(ClauseParser):
    def __init__(self):
        super(AggClauseParser, self).__init__()
        self.clause = ""
    def pre_treatment(self, clause):
        self.clause = clause
    def process_clause(self):
        return self.get_es_agg_string(self.clause)

    def get_es_agg_string(self, s):
        s = s.replace(' ','')
        ts = s.split(';')
        re = '"aggs":{'
        for x in ts:#处理每个agg
            s = x.split(',')
            for y in s:#处理每个agg中的kv
                s1 = y.split(':')
                if s1[0]=='group_key':
                    re +='"group_'+s1[1]+'":{"term":{"field":"'+s1[1]+'"},'+'"aggs":{'
                elif s1[0]=='agg_fun':
                    s2=s1[1].split('#')
                    for z in s2:#fun部分循环处理
                        if z[:3]=='cou':
                            continue
                        else:
                            re+='"'+z[:3]+'_'+z[4:-1]+'":{'+'"'+z[:3]+'":{"field":"'+z[4:-1]+'"}},'
                    re = re[:-1]+'}'
                else:
                    print 'error:%s' % s
                    float("error")
            re+='},'
            if re[-4]==':' and re[-3]=='}':#如果aggs部分为空，特殊处理
                re = re[:-11]+re[-2:]
        re = re[:-1]+'}'#去掉， 添加}
        return re

if "__main__" == __name__:
    parsers = {
        "query":QueryClauseParser(),
        "filter":FilterClauseParser(),
        "sort":SortClauseParser(),
        "agg":AggClauseParser()}
    
    print parsers[sys.argv[1]].parse_clause(sys.argv[2])
