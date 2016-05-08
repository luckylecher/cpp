#! /usr/bin/python

import os
import file_util
import common
import ainst_logging
from logger import Log

def initLogging(ainstConf, verbose):
    if not ainstConf:
        return False
    userLogLevel = 'info'
    if verbose:
        userLogLevel = 'debug'
    if not ainst_logging.init(ainstConf.logfile, ainstConf.loglevel,
                              userLogLevel):
        return False
    return True

def getInstallRoot(installRoot=None, ainstConf=None):
    if installRoot is None:
        if os.environ.has_key(common.AINST_DEFAULT_INSTALLROOT):
            installRoot = os.environ[common.AINST_DEFAULT_INSTALLROOT]
        if installRoot:
            Log.cout(Log.INFO, 'Notice: no --installroot, will use: %s'\
                         % installRoot)
        elif ainstConf and ainstConf.installroot:
            installRoot = ainstConf.installroot
            Log.cout(Log.INFO, 'Notice: no --installroot, will use default: %s'\
                         % installRoot)
    if installRoot:
        installRoot = file_util.getAbsPath(installRoot)
    return installRoot


