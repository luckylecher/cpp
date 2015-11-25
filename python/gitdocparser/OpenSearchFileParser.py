#coding:utf-8
import os,sys,logging
import codecs,re,HTMLParser,time
import json
from DocUploader import OpenSearchDocUploader
import commands
from logger import Logger
DEBUG = False
class OpenSearchFileParser:
    def __init__(self, config_file):
        self.config_file = config_file
        self.flist = {}
        self.finalList = []
        self.initConfig()
        self.logger = Logger()
        self.uploader = OpenSearchDocUploader(self.appName, self.ak, self.secret, self.appHost, self.logger, self.naviMap)
        
        
    def initConfig(self):
        configObj = json.load(open(self.config_file))
        self.appName = configObj['app_name']
        self.gitDir = configObj['git_dir']
        self.docDir = os.path.join(self.gitDir, "doc")
        self.pubTag = configObj['outer_tag']
        self.tunTag = configObj['inner_tag']
        self.urlPrefix = configObj['url_prefix']
        self.ak = configObj['access_key']
        self.secret = configObj['secret']
        self.appHost = configObj['app_host']
        self.naviMap = configObj['navigate_code']
        if not self.urlPrefix.endswith("/"):
            self.urlPrefix += "/"
        self.indexFileName = configObj['index_file_name']

    def getUpdateFromGitLabServer(self):
        cmd = "cd %s && git pull" % self.gitDir
        self.logger.info(cmd)
        st, out = commands.getstatusoutput(cmd)
        self.logger.info( "git status: " + out )
        if st != 0:
            self.logger.error( "Command execute failed, program exit!" )
            return False
        if out.startswith("Already up-to-date."):
            self.logger.info( "Git doc content not change, program exit!" )
            return False
        return True

    def startUp(self):
        if not self.getUpdateFromGitLabServer():
            return
        indexObj = self.processIndexFile(os.path.join(self.docDir, self.indexFileName))
        self.generateIndexDict("", "", "", indexObj)
        self.processFileList()
        self.readFileInFinalList()

    #git帮助文件夹的根目录,下一级目录内容包含doc
    def setGitDirFile(self, gitDir):
        self.gitDir = gitDir
        self.docDir = os.path.join(self.gitDir, "doc")

    #给每一项增加一个raw_url,保存其路径
    def generateIndexDict(self, path_prefix, url_prefix, title_prefix, indexObj):
        for item in indexObj:
            item['raw_url'] = url_prefix + "/" + item['name_en']
            if title_prefix != "":
                item['navigation'] = title_prefix + " > " + item['name_cn']
            else:
                item['navigation'] = item['name_cn']
            self.flist[path_prefix + item['key']] = item

    def cutNavigationLastSegment(self, naviStr):
        if naviStr.find('>') < 0:
            return naviStr
        else:
            return naviStr[:naviStr.rfind('>')]

    #处理flist中的每一个元素,生成finalList表
    def processFileList(self):
        while len(self.flist) > 0:
            last = self.flist.popitem()
            if not last[1]['isFolder']:
                last[1]['navigation'] = self.cutNavigationLastSegment(last[1]['navigation'])
                self.finalList.append((last[0],last[1]))
                continue
            indexObj = self.processIndexFile(os.path.join(self.docDir, last[0] + "/" + self.indexFileName))
            self.generateIndexDict(last[0] + "/", last[1]['raw_url'], last[1]['navigation'], indexObj)

    #格式化index.json中的内容成对象
    def processIndexFile(self, path):
        fp = file(path)
        ctn = fp.read()
        ctn = ctn[ctn.find("["):]
        indexObj = json.loads(ctn)
        return indexObj

    #从构造好的文件列表中遍历读取文档并处理
    def readFileInFinalList(self):
        i = 1
        for item in self.finalList:
            docInfo = {
                "abstract": u"",
                "tag": u"all",
                "content": u"",
                "link_suffix": u"",
                "id": "",
                "md5": "",
                "title": ""
            }
            if self.pubTag in item[1]['tag']:
                docInfo['tag'] = self.pubTag
            elif self.tunTag in item[1]['tag']:
                docInfo['tag'] = self.tunTag
            f = codecs.open(os.path.join(self.docDir, item[0] + ".md"), "r", "utf-8")
            for line in f:
                if line.startswith(u"# ") or line.startswith(u"## ") or line.startswith(u"### "):
                    docInfo['abstract'] += line.replace("#","").replace("\r\n", " ").replace("\n", " ")
                docInfo['content'] += self.formatLineContent(line)
            if docInfo['title'] == "":
                docInfo["title"] = item[1]['name_cn']
            docInfo['navigation'] = item[1]['navigation']
            if DEBUG:
                print docInfo['content']
            docInfo['link_suffix'] = self.convert2URLSuffix(item[1]['raw_url'])
            self.uploader.uploadDoc(docInfo)

    #将文档路径转换成内网URL后缀
    def convert2URLSuffix(self, path):
        path = path[1:]
        lastSlash = path.rfind("/")
        firstSlash = path.find("/")
        if lastSlash != firstSlash:
            path = path[:lastSlash] + u"&" + path[lastSlash + 1:]
        return path


    #去除markdown格式,转义html标签,输出处理后的文本
    def formatLineContent(self, line):
        #print line
        if line.startswith("|"):
            line = re.sub(re.compile(r"(\s?\:?-*\s?\|\s?-+\s?){0,}\|"), " ", line)
        line = re.sub(re.compile(r"\(\{\{.*?\}\}\)"), "", line)
        line = re.sub(re.compile(r"^\#+ "), "", line)
        line = re.sub(re.compile(r"<(\/font|font|br).*?>"), "", line)
        line = re.sub(re.compile(r"\(http://.*?\)"), "", line)
        line = re.sub(re.compile(r"^\s?\* "), "", line)
        line = line.replace("```","").replace("**","").replace("&lt;","<")\
               .replace("&gt;",">").replace("&quote;",'"').replace("&quot;",'"')
        line = line.replace("\\*","*").replace("\\+","+").replace("\\-","-")\
               .replace("\\=","=").replace("\\_","_")
        #print line
        line = line.replace("![]","")
        line = line.replace("\\u","\\ u").replace("\\x", "\\ x")\
                            .replace("\t","    ").replace("\r\n","  ")\
                            .replace("\n","  ")
        return line

if __name__ == "__main__":
    #1个参数:配置文件所在路径
    ofp = OpenSearchFileParser(sys.argv[1])
    ofp.startUp()
