#coding:utf-8
import os,logging
class Logger:
    def __init__(self):
        logging.basicConfig(filename = os.path.join(os.getcwd(), 'rt_log.txt'), 
                            level = logging.INFO, filemode = 'a',
                            format = '%(asctime)s - %(levelname)s: %(message)s')
    def info(self, str):
        logging.info(str)

    def error(self, str):
        logging.error(str)
