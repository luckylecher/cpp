#import xml.etree.ElementTree as ET

class Item:
    def __init__(self, value, name):
        self._value = value
        self._name = name

class Node:
    def __init__(self):
        self.nodes = []
        self.tags = {}

    def analyze(self, node):
        for child in node:
            if self.hasChild(child):
                node = Node()
                node.analyze(child)
                self.nodes.append(node)
            else:
                item = Item(self.text, self.attrib['name'])
                self.tags[self.tag].append(item)

    def hasChild(self, node):
        return len(node) > 0
    
