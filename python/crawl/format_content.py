#coding:utf-8
import codecs
class FormatDoc:
    def __init__(self):
        self.counter = 0
        self.category = {
            "brief-manual":1,
            "quick-start":2,
            "api-reference":3,
            "sdk":4,
            "best-practice":5
        }
        self.pre_category = -1

    def beginFormat(self, input_file="html.converted.txt", output_file="html.final.txt"):
        f = codecs.open(input_file, "r", encoding="utf-8", errors="ignore")
        ff = codecs.open(output_file, "w", encoding="utf-8", errors="ignore")
        docContent = ""
        docTitle = ""
        for line in f:
            if line.startswith("yhb~"):
               docContent=""
            elif line.startswith("link="):
                docUrl = line[5:-1].replace("^_","")

                print docUrl
                ff.write(self.deal_a_doc(docContent,docUrl, docTitle))
                docTitle = ""
            elif line.startswith("doc_title="):
                docTitle = line[10:-1].replace("^_","")
            else:
                docContent += line
        print "total:%d" % self.counter
        f.close()
        ff.close()

    def deal_a_doc(self, doc, url, title):
        if title == "":
            title = u"待补充"
        self.counter += 1
        url_parts = url.split("/")
        if len(url_parts) < 8:
            print url
            return None
        last_part = url_parts[7]
        main_id = self.category[url_parts[6]] * 1000 + self.counter
        return "doc_id=%d\ndoc_title=%s\ndoc_content=%s\ndoc_link=%s\n" % (main_id, title, doc,url)

if "__main__" == __name__:
    FormatDoc().deal()