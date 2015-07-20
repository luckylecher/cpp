#!/bin/bash

cd /root/crawler/news
/usr/local/bin/scrapy crawl jsonnews

if [ $? -ne 0 ]
then
    echo 'Crawl sinanews failed!'
fi
