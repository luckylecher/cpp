#encoding:utf-8
import hashlib,sys
class MakeJsonFile:
    def __init__(self):
        self.fpath = ""
        self.outpath = ""
    def deal(self):
        f = open(self.fpath)
        id = 0
        title = ""
        content = ""
        link = ""
        statu = 0
        counter = 0
        all = "["
        for line in f:
            if statu == 0:
                if line.startswith("id="):
                    id = line.rstrip()[3:]
                    statu = 1
            elif statu == 1:
                if line.startswith("title="):
                    title = line.rstrip()[6:]
                    statu = 2
            elif statu == 2:
                if line.startswith("content="):
                    content = line[8:]
                    statu = 3
                else:
                    title += line
            elif statu == 3:
                if line.startswith("link="):
                    link = line.rstrip()[5:]
                    m = hashlib.md5()
                    m.update(link.split("/").pop())
                    link_hash = m.hexdigest()
                    all += self.generateItem(id,title,content,link,link_hash)
                    counter += 1
                    statu = 0
                else:
                    content += line
        all = all[:-1]
        all += "]"
        print "有%d条数据被处理了" % counter
        f.close()
        f = open(self.outpath, "w")
        f.write(all)
        f.close()
                    
    def setPath(self,path):
        self.fpath = path
        self.outpath = path + ".os.txt"
        
    def generateItem(self, id, title, content, link, link_hash, navi="OpenSearch 帮助文档"):
        return '{"fields":{"id":"%s","title":"%s","content":"%s","link":"%s","link_hash":"%s","navigator":"%s"},"cmd":"ADD"},' % (id, title, content
                                                                                                .replace("\\","\\\\").replace("\\x", "\\ x")
                                                                                                .replace("\"","\\\"")
                                                                                                .replace("\t","    ")
                                                                                                .replace("\n","\\n"), link,link_hash,navi)

if __name__ == "__main__":
    mjf = MakeJsonFile()
    fname = sys.argv[1]
    mjf.setPath(fname)
    mjf.deal()
