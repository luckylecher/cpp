#!/usr/bin/python
#coding:utf-8
import sys
import commands

dir = "/Users/licheng/Documents/git/cpp/python/test/gittest/1-2"

def a():
    cmd = "cd %s && git pull" % dir
    print cmd
    print commands.getstatusoutput(cmd)

a()
