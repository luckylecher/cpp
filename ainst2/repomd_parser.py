#! /usr/bin/python

from xml_parser import XmlParser
from xml.sax import handler
from logger import Log
from repo_data import RepoMdData, RepoMd

class RepoMdSaxHandler(handler.ContentHandler):
    def __init__(self):
        self.repomd = RepoMd()
        self.currentData = None
        self.currentTag = ''
        self.inTag = False

    def startElement(self, name, attrs):
        self.currentTag = name
        self.inTag = True
        if name == 'data':
            self.currentData = RepoMdData()
            if attrs.has_key('type'):
                self.currentData.type = attrs.getValueByQName('type')
        elif name == 'location' and self.currentData:
            if attrs.has_key('href'):
                self.currentData.locationHref = attrs.getValueByQName('href')
        elif name == 'checksum' and self.currentData:
            if attrs.has_key('type'):
                self.currentData.checksumType = attrs.getValueByQName('type')
        elif name == 'open-checksum' and self.currentData:
            if attrs.has_key('type'):
                self.currentData.openchecksumType = \
                    attrs.getValueByQName('type')

    def endElement(self, name):
        if name == 'data' and self.currentData:
            self.repomd.repoMdDatas[self.currentData.type] = self.currentData
        self.inTag = False

    def characters(self, content):
        if not self.inTag:
            return
        if self.currentTag == 'checksum':
            self.currentData.checksumValue = content
        elif self.currentTag == 'timestamp':
            self.currentData.timestamp = content
        elif self.currentTag == 'open-checksum':
            self.currentData.openchecksumValue = content


class RepoMdParser:
    def __init__(self):
        self.parser = XmlParser()
        self.handler = RepoMdSaxHandler()
        self.parser.setContentHandler(self.handler)

    def parse(self, fileName):
        if self.parser.parse(fileName):
            return self.handler.repomd
        Log.cout(Log.ERROR, 'Parse repomd [%s] failed' % fileName)
        return None
