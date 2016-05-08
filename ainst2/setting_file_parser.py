#! /usr/bin/python

import ConfigParser

class SettingFileParser:
    def parse(self, fileName):
        configParser = ConfigParser.ConfigParser()
        content = None
        try:
            content = configParser.read(fileName)
        except Exception:
            return None
        settings = {}
        sections = configParser.sections()
        if not content or not sections:
            return settings
        for section in  sections:
            keyValue = {}
            for key, value in configParser.items(section):
                keyValue[key] = value
            settings[section] = keyValue
        return settings

if __name__ == '__main__':
    fileName = './ini'
    parser = SettingFileParser()
    print parser.parse(fileName)
    
