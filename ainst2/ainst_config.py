#! /usr/bin/python

import os

class AinstConfig:
    def __init__(self):
        self.reposdir = ['/etc/yum/repos.d', '/etc/yum.repos.d/']
        self.installonlypkgs = ['kernel', 'kernel-bigmem',
                                'kernel-enterprise','kernel-smp',
                                'kernel-modules', 'kernel-debug',
                                'kernel-unsupported', 'kernel-source',
                                'kernel-devel', 'kernel-PAE',
                                'kernel-PAE-debug']
        self.exactarchlist = ['kernel', 'kernel-smp', 'kernel-hugemem',
                              'kernel-enterprise', 'kernel-bigmem',
                              'kernel-devel', 'kernel-PAE', 'kernel-PAE-debug']
        self.exactarch =1
        self.timeout = 30.0
        self.installroot = None
        self.ainstroot = '/var/ainst2/'
        self.rootinfo = self.ainstroot + '/root.info'
        self.cachedir = self.ainstroot + '/cache/'
        self.keepcache = 1
        self.expiretime = 3600
        self.maxfilelength = 1024 * 1024 * 1024 * 2
        self.retrytime = 3
        self.sockettimeout = 5
        self.logfile = '/var/ainst2/ainst.log'
        self.loglevel = 'debug'
        self.autostart = True
        self.distroverpkg = 'redhat-release'
        self.basearch = 'x86_64'
        self.arch = 'ia32e'
        self.releasever = '5Server'
        self.repoConfigItems = {}

    def getRepoConfigItem(self, itemName):
        if self.repoConfigItems.has_key(itemName):
            return self.repoConfigItems[itemName]
        return None


class RepoConfigItem:
    def __init__(self):
        self.name = ''
        self.enabled = 1
        self.baseurl = ''
        self.mirrorlist = ''
        self.gpgcheck = 0
