#encoding:utf-8
#__author__ = 'licheng'
from selenium_crawler import SCrawler
from remove_html_tags import HtmlTagRemover
from format_content import FormatDoc
from data_maker import MakeJsonFile
class DataUpdateController:
    def __init__(self):
        self.crawler = SCrawler()
        self.file = "docs/html.txt"
        self.html_tag_ramover = HtmlTagRemover()
        self.dest_file = self.file[:-4] + ".converted.txt"
        self.final_file = self.file[:-4] + ".final.txt"
        self.doc_formater = FormatDoc()
        self.data_uploader = MakeJsonFile()

    def beginCrawlData(self):
        self.crawler.start_crawler(self.file)

    def convertData(self):
        self.html_tag_ramover.beginRemoveTags(self.file, self.dest_file)

    def formatContent(self):
        self.doc_formater.beginFormat(self.dest_file, self.final_file)

    def uploadToOpensearch(self):
        self.data_uploader.setPath(self.final_file)
        self.data_uploader.entrancy()

    def startSystem(self):
        #self.beginCrawlData()
        self.convertData()
        self.formatContent()
        self.uploadToOpensearch()

    def test(self):
        self.uploadToOpensearch()

if "__main__" == __name__:
    DataUpdateController().startSystem()
