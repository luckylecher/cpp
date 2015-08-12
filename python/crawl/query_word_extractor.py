#coding:utf-8
import commands,re
class Extractor:
    def __init__(self):
        pass
    def setFile(self, f):
        self.f = f
    def curlAliws(self, query):
        cmd = "curl 'http://bj-algo.proxy.taobao.org/aliws_demo/aliws_demo.php?keyword=%s'" % query
        status, res = commands.getstatusoutput(cmd)
        pattern = re.compile(r"<tr><td.*?>(.*?)</td>")
        words = pattern.findall(res)
        for item in words:
            print item
        return words
    def start(self):
        f = open(self.f)
        for line in f:
            if line.startswith("name="):
                self.curlAliws(line.split("=")[1])

if "__main__" == __name__:
    ex = Extractor()
    ex.setFile("name")
    ex.start()