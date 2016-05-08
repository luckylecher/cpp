#coding:utf-8
import sys
import re
url = {
    "10.125.224.84":"http://10.125.224.79/amonitor/service_view/?sn=open_search_perf_84&sst=%s&set=%s&cni=0_4&cmi=0_7N42iuu26oVKQuXOM1Pzgs&avg=true&display=50&nst=1439803546&net=1439803726",
    "10.125.224.82":"http://10.125.224.79/amonitor/service_view/?sn=open_search_ha3_perf&sst=%s&set=%s&cni=0_a&cmi=0_7N42ipuUJwthUgk1YE2Flm&avg=true&display=50&nst=1439372984&net=1439373284",
    "10.101.169.82":"http://10.125.224.79/amonitor/service_view/?sn=open_search_ha3_perf&sst=%s&set=%s&cni=0_a&cmi=0_7N42ipuUJwthUgk1YE2Flm&avg=true&display=50&nst=1439372984&net=1439373284",
    "10.125.224.27":"http://10.125.224.79/amonitor/service_view/?sn=open_search_ha3_perf&sst=%s&set=%s&cni=0_i&cmi=0_7N42ipBm0N6DaYxMcAF8Vq&avg=true&display=50&nst=1439445658&net=1439445958"
    }
dir = "/Users/licheng/Documents/git/elasticsearch_perf_test/perf_test_result/111957_es_os/os/%s/%s/parallel_%s/os/1.txt"

    
map = {
    "sq":"single_query",
    "dq":"double_query",
    "agg":"query_with_agg",
    "ft":"query_with_filter",
    "st":"query_with_sort",
    "fd":"filter_by_distance",
    "sd":"sort_by_distance"
    }

if "__main__" == __name__:
    datasize = sys.argv[1]
    typ = sys.argv[2]
    para = sys.argv[3]
    if sys.argv[4] == "99141":
        dir = dir.replace("111957_es_os", "99141")
        
    f = open(dir % (datasize, map[typ], para))
    ctn = f.read()
    res = re.compile(r"FROM\((.*?)\) TO\((.*?)\)").findall(ctn)
    ips = re.compile(r"--http (.*?) ").findall(ctn)
    print res
    print ips
    x = url[ips[ len(ips) -1 ]]
    print x % (res[ len(res) - 1 ][0].replace(" ","%20"), res[ len(res) - 1 ][1].replace(" ","%20"))
