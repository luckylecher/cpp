#! /usr/bin/python

import os
import rpmutils
import file_util
from logger import Log
from aicf import AicfParser
from repository import FakeRepository
from rpm_header_package import LocalRpmPackage, AinstRpmPackage
from ainst_root import AinstRoot, AinstRootReader
from package_sack import PackageSack

class AinstPackageSackBuilder:
    def __init__(self, installRoot):
        self._installRoot = installRoot

    def buildActivePkgSack(self):
        sack = PackageSack()
        ainstRoot = AinstRoot(self._installRoot)
        if not ainstRoot.isValidAinstRoot():
            Log.cout(Log.DEBUG, '%s is invalid ainst root' % self._installRoot)
            return None
        reader = AinstRootReader(ainstRoot)
        activePkgMetas = reader.getActivePkgMetas()
        if activePkgMetas is None:
            Log.cout(Log.DEBUG, 'Get active meta of %s failed' % self._installRoot)
            return None
        for pkgName, rpmPath, aicfPath in activePkgMetas:
            aicfInfo = None
            if file_util.isFile(aicfPath):
                aicfInfo = AicfParser().parse(aicfPath)
            header = rpmutils.readRpmHeader(rpmPath)
            if header:
                repo = FakeRepository(self._installRoot, True)
                pkg = AinstRpmPackage(header, repo, aicfInfo)
                sack.addPackageObject(pkg)
        return sack

    def buildInstalledPkgSack(self):
        sack = PackageSack()
        ainstRoot = AinstRoot(self._installRoot)
        if not ainstRoot.isValidAinstRoot():
            Log.cout(Log.DEBUG, '%s is invalid ainst root' % self._installRoot)
            return None
        reader = AinstRootReader(ainstRoot)
        installPkgMetas = reader.getInstallPkgMetas()
        if installPkgMetas is None:
            Log.cout(Log.DEBUG, 'Get install meta of %s failed' % self._installRoot)
            return None
        for pkgVer, rpmPath in installPkgMetas:
            header = rpmutils.readRpmHeader(rpmPath)
            if header:
                repo = FakeRepository(self._installRoot, True)
                pkg = AinstRpmPackage(header, repo)
                sack.addPackageObject(pkg)
        return sack

    def buildInstalledPkgRepoSack(self):
        sack = PackageSack()
        ainstRoot = AinstRoot(self._installRoot)
        if not ainstRoot.isValidAinstRoot():
            Log.cout(Log.DEBUG, '%s is invalid ainst root' % self._installRoot)
            return None
        reader = AinstRootReader(ainstRoot)
        installPkgMetas = reader.getInstallPkgMetas()
        if installPkgMetas is None:
            Log.cout(Log.DEBUG, 'Get install meta of %s failed' % self._installRoot)
            return None
        for pkgVer, rpmPath in installPkgMetas:
            pkg = LocalRpmPackage(rpmPath)
            if pkg.init():
                sack.addPackageObject(pkg)
        return sack

