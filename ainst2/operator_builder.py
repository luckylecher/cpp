#! /usr/bin/python

import os
import file_util
import common
from logger import Log
from ainst_root import AinstRoot
from ainst_operator import AinstOperator
from root_ainst_operator import RootAinstOperator
from local_ainst_operator import LocalAinstOperator

class InstallRootType:
    NO_INSTALLROOT = 0
    MUST_INSTALLROOT = 1
    ANY_INSTALLROOT = 2

def getAinstOperator(ainstConf, installRoot=None,
                     installRootType=InstallRootType.MUST_INSTALLROOT):
    if not ainstConf:
        Log.cout(Log.ERROR, "Ainst config is None")
        return None

    if installRootType == InstallRootType.NO_INSTALLROOT:
        return AinstOperator(ainstConf)

    if installRootType == InstallRootType.MUST_INSTALLROOT and not installRoot:
        Log.cout(Log.ERROR, "Install root is invalid")
        return None
    
    if installRoot == '/':
        return RootAinstOperator(ainstConf, installRoot)

    ainstRoot = AinstRoot(installRoot)
    return LocalAinstOperator(ainstConf, installRoot, ainstRoot)
