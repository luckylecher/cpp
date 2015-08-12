#coding:utf-8
import os
import codecs,re,HTMLParser,time
import json
from DocUploader import OpenSearchDocUploader
class OpenSearchFileParser:
    def __init__(self):
        self.indexFileName = "index.json"
        self.flist = {}
        self.finalList = []
        self.urlPrefix = "https://docs.aliyun.com/#/pub/opensearch/"
        self.test = codecs.open("docs/allmd.txt", "w", "utf-8")
        self.uploader = OpenSearchDocUploader()
        self.pubTag = "pub"
        self.tunTag = "tun"

    #git帮助文件夹的根目录,下一级目录内容包含doc
    def setRootFile(self, root):
        self.root = root
        self.docDir = os.path.join(self.root, "doc")

    def getAllHelpFiles(self):
        indexObj = self.processIndexFile(os.path.join(self.docDir, self.indexFileName))
        self.generateIndexDict("", "", indexObj)
        self.processFileList()
        self.readFileInFinalList()

    #给每一项增加一个raw_url,保存其路径
    def generateIndexDict(self, path_prefix, url_prefix, indexObj):
        for item in indexObj:
            item['raw_url'] = url_prefix + "/" + item['name_en']
            self.flist[path_prefix + item['key']] = item

    #处理flist中的每一个元素,生成finalList表
    def processFileList(self):
        while len(self.flist) > 0:
            last = self.flist.popitem()
            if not last[1]['isFolder']:
                self.finalList.append((last[0],last[1]))
                continue
            indexObj = self.processIndexFile(os.path.join(self.docDir, last[0] + "/index.json"))
            self.generateIndexDict(last[0] + "/", last[1]['raw_url'], indexObj)

    #格式化index.json中的内容成对象
    def processIndexFile(self, path):
        fp = file(path)
        ctn = fp.read()
        ctn = ctn[ctn.find("["):]
        indexObj = json.loads(ctn)
        return indexObj

    #从构造好的文件列表中遍历读取文档并处理
    def readFileInFinalList(self):
        for item in self.finalList:
            docInfo = {
                "abstract": "",
                "tag": "all",
                "content": ""
            }
            if self.pubTag in item[1]['tag']:
                docInfo['tag'] = self.pubTag
            elif self.tunTag in item[1]['tag']:
                docInfo['tag'] = self.tunTag
            f = codecs.open(os.path.join(self.docDir, item[0] + ".md"), "r", "utf-8")
            for line in f:
                if line.startswith(u"# ") or line.startswith(u"## ") or line.startswith(u"### "):
                    docInfo['abstract'] += line.replace("#","")
                docInfo['content'] += self.removeMdElements(line)
            docInfo["title"] = item[1]['name_cn']
            self.uploadDoc(item[1]['raw_url'])
            #self.test.write(content)

    #将文档路径转换成内网URL
    def convert2URL(self, path):
        path = path[1:]
        lastSlash = path.rfind("/")
        firstSlash = path.find("/")
        if lastSlash != firstSlash:
            path = path[:lastSlash] + u"&" + path[lastSlash + 1:]
        return self.urlPrefix + path

    def uploadDoc(self, path, docObj):
        url = self.convert2URL(path)
        docObj['link'] = url
        self.uploader.uploadDoc(docObj)

    #去除markdown格式,转义html标签,输出处理后的原始文本
    def removeMdElements(self, line):
        #print line
        if line.startswith("|"):
            line = re.sub(re.compile(r"(\s?\:?-*\s?\|\s?-+\s?){0,}\|"), " ", line)
        line = re.sub(re.compile(r"\(\{\{.*?\}\}\)"), "", line)
        line = re.sub(re.compile(r"^\#+ "), "", line)
        line = re.sub(re.compile(r"<(\/font|font|br).*?>"), "", line)
        line = re.sub(re.compile(r"\(http://.*?\)"), "", line)
        line = re.sub(re.compile(r"^\s?\* "), "", line)
        line = line.replace("```","").replace("**","").replace("&lt;","<").replace("&gt;",">").replace("&quote;",'"').replace("$quot",'"')
        line = line.replace("\\*","*").replace("\\+","+").replace("\\-","-").replace("\\=","=").replace("\\_","_")
        #print line
        return line.replace("![]","")

if __name__ == "__main__":
    ofp = OpenSearchFileParser()
    ofp.setRootFile("/Users/licheng/Documents/git/opensearch")
    ofp.getAllHelpFiles()
