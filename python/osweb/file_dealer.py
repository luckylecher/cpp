#encoding:utf-8
class MakeJsonFile:
    def __init__(self):
        self.fpath = ""
    def deal(self):
        f = open(self.fpath)
        id = 0
        title = ""
        content = ""
        link = ""
        statu = 0
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
                    all += self.generateItem(id,title,content,link)
                    statu = 0
                else:
                    content += line
        all = all[:-1]
        all += "]"
        f.close()
        f = open("output.txt", "w")
        f.write(all)
        f.close()
                    
    def setPath(self,path):
        self.fpath = path
        
    def generateItem(self, id, title, content, link):
        return '{"fields":{"id":"%s","title":"%s","content":"%s","link":"%s"},"cmd":"ADD"},' % (id, title, content
                                                                                                .replace("\\","\\\\")
                                                                                                .replace("\"","\\\"")
                                                                                                .replace("\t","    ")
                                                                                                .replace("\n","\\n"), link)

if __name__ == "__main__":
    mjf = MakeJsonFile()
    mjf.setPath("temp.txt")
    mjf.deal()
