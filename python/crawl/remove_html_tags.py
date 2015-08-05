#coding:utf-8
import codecs,re,HTMLParser
class HtmlTagRemover:

    def replace_all(self, str):
        return re.compile(r"<.*?>").sub("",str)

    def beginRemoveTags(self, file="html.txt", dest_file="html.converted.txt"):
        f = codecs.open(file, "r",encoding="utf-8",errors="replace")
        str = ""
        html_escaper = HTMLParser.HTMLParser()
        for line in f:
            temp = self.replace_all(line.replace("<h1","\ntitle=<h1"))
            str += html_escaper.unescape(temp)
        f.close()
        f = codecs.open(dest_file, "w", encoding="utf-8", errors="ignore")
        f.write(str)
        #print re.findall(re.compile(r"url=https://.*?\n"),str)

