#! /usr/bin/python

from xml.sax import make_parser, parse, SAXException
from logger import Log

class XmlParser:
    def __init__(self):
        self.parser = make_parser()
        
    def setContentHandler(self, handler):
        self.parser.setContentHandler(handler)
    
    def parse(self, fileName):
        try:
            self.parser.parse(fileName)
        except SAXException,e:
            Log.cout(Log.ERROR, e)
            return False
        return True
