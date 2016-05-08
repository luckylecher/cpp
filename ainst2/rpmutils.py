#! /usr/bin/python 

import os
import re
import rpm
import process
import file_util
from arch import isValiedArch
from logger import Log

def compareEVR((e1, v1, r1), (e2, v2, r2)):
    """
    # return 1: a is newer than b
    # 0: a and b are the same version
    # -1: b is newer than a
    """
    (e1, v1, r1) = (str(e1), str(v1), str(r1))
    (e2, v2, r2) = (str(e2), str(v2), str(r2))
    return rpm.labelCompare((e1, v1, r1), (e2, v2, r2))

def splitFileName(filename):
    """
    Pass in a standard style rpm fullname 
    """
    if not filename.endswith('.rpm'):
        return None
    filename = filename[:-4]
    return splitPkgName(filename)

def splitPkgName(pkgName):
    epoch, name, ver, rel, arch = None, None, None, None, None
    epochIndex = pkgName.find(':')
    if epochIndex != -1:
        epoch = pkgName[:epochIndex]
        pkgName = pkgName[epochIndex+1:]

    nameIndex = pkgName.find('-')
    if nameIndex == -1:
        name = pkgName
        return name, ver, rel, epoch, arch
    name = pkgName[:nameIndex]
    pos = nameIndex + 1
    
    verIndex = pkgName[pos:].find('-')
    if verIndex == -1:
        ver = pkgName[pos:]
        return name, ver, rel, epoch, arch
    ver = pkgName[pos:pos+verIndex]
    pos = pos + verIndex + 1

    relIndex = pkgName[pos:].find('.')
    if relIndex == -1:
        rel = pkgName[pos:]
        return name, ver, rel, epoch, arch
    rel = pkgName[pos:pos+relIndex]

    pos = pos + relIndex + 1
    arch = pkgName[pos:]
    return name, ver, rel, epoch, arch

def pkgTupleFromHeader(hdr):
    """return a pkgtuple (n, a, e, v, r) from a hdr object, converts
    None epoch to 0, as well.
    """
    name = hdr['name']
    version = hdr['version']
    release = hdr['release']
    epoch = hdr['epoch']
    if epoch is None:
        epoch = '0'
    if hdr[rpm.RPMTAG_SOURCERPM] or hdr[rpm.RPMTAG_SOURCEPACKAGE] != 1:
        arch = hdr['arch']
    else:
        arch = 'src'
    return (name, arch, epoch, version, release)

def readRpmHeader(filename):
    """Read an rpm header """
    ts = rpm.TransactionSet()
    header = _doReadRpmHeader(ts, filename)
    if not header:
        ts.setVSFlags(-1)
        header = _doReadRpmHeader(ts, filename)
    return header

def _doReadRpmHeader(ts, filename):
    try:
        fd = os.open(filename, os.O_RDONLY)
    except OSError, e:
        return None

    header = None
    try:
        header = ts.hdrFromFdno(fd)
    except rpm.error, e:
        os.close(fd)
        return None
    if type(header) != rpm.hdr:
        return None
    return header

def checkRange(requireTuple, pkgTuple):
    """returns true if the package epoch-ver-rel satisfy the range
       requested in the reqtuple:
       ex: foo >= 2.1-1"""
    (n, f, e, v, r) = pkgTuple
    return compareRange(requireTuple, (n, 'EQ', (e, v, r)))

def compareRange(requireTuple, provTuple):
    """returns true if provtuple satisfies reqtuple
       requireTuple and provTuple contains (n, f, e, v, r)
    """
    (reqn, reqf, (reqe, reqv, reqr)) = requireTuple
    (n, f, (e, v, r)) = provTuple

    if reqn != n:
        return 0
    if f is None or reqf is None:
        return 1

    # ie: if the request is EQ foo 1:3.0.0 and we have 
    # foo 1:3.0.0-15 then we have to drop the 15 so we can match
    if reqr is None:
        r = None
    if reqe is None:
        e = None
    # just for the record if ver is None then we're going to segfault
    if reqv is None:
        v = None
    # if we just require foo-version, then foo-version-* will match
    if r is None:
        reqr = None

    rc = compareEVR((e, v, r), (reqe, reqv, reqr))

    # method : find the intersection of requireTuple and provideTuple
    # provTuple (e, v, r) is newer
    if rc >= 1:
        if reqf in ['GT', 'GE', 4, 12]:
            return 1
        elif reqf in ['LE', 'LT', 'EQ', 10, 2, 8]:
             if f in ['LE', 'LT', 10, 2]:
                 return 1

    # (e, v, r) is equal
    elif rc == 0:
        if reqf in ['GT', 4]:
            if f in ['GT', 'GE', 4, 12]:
                return 1
        elif reqf in ['GE', 12]:
            if f in ['GT', 'GE', 'EQ', 'LE', 4, 12, 8, 10]:
                return 1
        elif reqf in ['EQ', 8]:
            if f in ['EQ', 'GE', 'LE', 8, 12, 10]:
                return 1
        elif reqf in ['LE', 10]:
            if f in ['EQ', 'LE', 'LT', 'GE', 8, 10, 2, 12]:
                return 1
        elif reqf in ['LT', 2]:
            if f in ['LE', 'LT', 10, 2]:
                return 1
    # require (e, v, r) is newer
    elif rc <= -1:
        if reqf in ['GT', 'GE', 'EQ', 4, 12, 8]:
            if f in ['GT', 'GE', 4, 12]:
                return 1
        elif reqf in ['LE', 'LT', 10, 2]:
            return 1
    return 0

def flagToString(flags):
    flags = flags & 0xf

    if flags == 0: return None
    elif flags == 2: return 'LT'
    elif flags == 4: return 'GT'
    elif flags == 8: return 'EQ'
    elif flags == 10: return 'LE'
    elif flags == 12: return 'GE'

    return flags

def stringToVersion(verstring):
    if verstring in [None, '']:
        return (None, None, None)
    i = verstring.find(':')
    if i != -1:
        try:
            epoch = str(long(verstring[:i]))
        except ValueError:
            # look, garbage in the epoch field, how fun, kill it
            epoch = '0' # this is our fallback, deal
    else:
        epoch = '0'
    j = verstring.find('-')
    if j != -1:
        if verstring[i + 1:j] == '':
            version = None
        else:
            version = verstring[i + 1:j]
        release = verstring[j + 1:]
    else:
        if verstring[i + 1:] == '':
            version = None
        else:
            version = verstring[i + 1:]
        release = None
    return (epoch, version, release)

def rpm2dir(rpmPath, destDir, timeout=600):
    currentWorkdir = os.getcwd()
    if not file_util.isDir(destDir) and not file_util.makeDir(destDir):
        Log.cout(Log.ERROR, 'Make rpm dir %s failed' % destDir)
        return False
    try:
        os.chdir(destDir)
    except OSError, e:
        return False
    cmd = 'rpm2cpio %s | cpio -ivd --no-absolute-filenames' % rpmPath
    out, err, code = process.runRedirected(cmd, timeout)
    if code != 0:
        Log.cout(Log.ERROR, 'Cpio [%s] result code: %d' % (rpmPath, code))
    try:
        os.chdir(currentWorkdir)
    except OSError, e:
        Log.cout(Log.ERROR, 'Chdir to %s failed' % currentWorkdir)
        return False
    return code == 0

def splitPkgName3(pkgName):
    epoch, name, ver, rel, arch = None, None, None, None, None
    # google-perftools-2.1-1.x86_64
    # anet-devel-1.3.3-rc_1.x86_64
    # AliWS-1.4.0.0-1.x86_64
    # python-2.4.3-27.el5.x86_64
    # copper-1.0.4-51.el5
    # openssl-devel-0.9.8e-22.el5.4.x86_64
    # libxml2-2.6.26-2.1.12.el5_7.2
    # tzdata-2011g-1.el5.x86_64
    # binutils-2.17.50.0.6-14.el5.x86_64
    
    verPattern = re.compile(r'(\S+)-(\d+\.\d+(?:(?:\.\d+)?(?:\.\d+)?\.\w+)?)-(\S+)')
    match = verPattern.match(pkgName)
    if not match:
        verPattern = re.compile(r'(\S+)-(\d+\.\d+(?:(?:\.\d+)?\.\w+)?)')
        match = verPattern.match(pkgName)
    if not match:
        verPattern = re.compile(r'(\S+)-(\S+)-(\d+\.\w+\d+.\w+)')
        match = verPattern.match(pkgName)
        
    if match:
        epochNameString = match.group(1)
        epochIndex = epochNameString.find(':')
        if epochIndex != -1:
            epoch = epochNameString[:epochIndex]
            name = epochNameString[epochIndex+1:]
        else:
            name = epochNameString
        ver = match.group(2)

        if len(match.groups()) > 2:
            relArchString = match.group(3)
            if relArchString:
                archIndex = relArchString.rfind('.')
                if archIndex != -1:
                    rel = relArchString[:archIndex]
                    arch = relArchString[archIndex+1:]
                    if not isValiedArch(arch):
                        # not a valid arch, maybe it is XXX-1.0-13.el5
                        rel = relArchString
                        arch = None
                else:
                    rel = relArchString
    else:
        epochNameString = pkgName
        epochIndex = epochNameString.find(':')
        if epochIndex != -1:
            epoch = epochNameString[:epochIndex]
            name = epochNameString[epochIndex+1:]
        else:
            name = epochNameString
    return name, ver, rel, epoch, arch


if __name__ == '__main__':
    pkgName = 'libgcc-4.1.2-46.el5.x86_64'
    assert(splitPkgName3(pkgName) == ('libgcc', '4.1.2', '46.el5', None, 'x86_64'))
    pkgName = 'redhat-release-5Server-5.4.0.3'
    assert(splitPkgName3(pkgName) == ('redhat-release-5Server', '5.4.0.3', None, None, None))
    pkgName = 'hippo-devel-0.1.0-pre1.x86_64'
    assert(splitPkgName3(pkgName) == ('hippo-devel', '0.1.0', 'pre1', None, 'x86_64'))
    pkgName = 'indexlib-debuginfo-1.9.0-nightly_201404221445.x86_64'
    assert(splitPkgName3(pkgName) == ('indexlib-debuginfo', '1.9.0', 'nightly_201404221445', None, 'x86_64'))
    pkgName = 't_search_cm2_hb_node_manager-0.3.0-41.x86_64'
    assert(splitPkgName3(pkgName) == ('t_search_cm2_hb_node_manager', '0.3.0', '41', None, 'x86_64'))
    pkgName = 'snappy-1.0.5-1.x86_64'
    assert(splitPkgName3(pkgName) == ('snappy', '1.0.5', '1', None, 'x86_64'))
    pkgName = 'google-perftools-2.1-1.x86_64'
    assert(splitPkgName3(pkgName) == ('google-perftools', '2.1', '1', None, 'x86_64'))
    pkgName = 'anet-devel-1.3.3-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('anet-devel', '1.3.3', 'rc_1', None, 'x86_64'))
    pkgName = 'libhdfs-cdh-2.0.2-0.x86_64'
    assert(splitPkgName3(pkgName) == ('libhdfs-cdh', '2.0.2', '0', None, 'x86_64'))
    pkgName = 'fslib-0.6.10-rc_3.x86_64'
    assert(splitPkgName3(pkgName) == ('fslib', '0.6.10', 'rc_3', None, 'x86_64'))
    pkgName = 'AliWS-1.4.0.0-1.x86_64'
    assert(splitPkgName3(pkgName) == ('AliWS', '1.4.0.0', '1', None, 'x86_64'))
    pkgName = 'alog-1.1.5-1.x86_64'
    assert(splitPkgName3(pkgName) == ('alog', '1.1.5', '1', None, 'x86_64'))
    pkgName = 'alog-devel-1.1.5-1.x86_64'
    assert(splitPkgName3(pkgName) == ('alog-devel', '1.1.5', '1', None, 'x86_64'))
    pkgName = 'protobuf-devel-2.4.2-rc_2.x86_64'
    assert(splitPkgName3(pkgName) == ('protobuf-devel', '2.4.2', 'rc_2', None, 'x86_64'))
    pkgName = 'deploy_express-0.10.0-rc_6.x86_64'
    assert(splitPkgName3(pkgName) == ('deploy_express', '0.10.0', 'rc_6', None, 'x86_64'))
    pkgName = 't_search_cm2_basic-0.3.0-72.x86_64'
    assert(splitPkgName3(pkgName) == ('t_search_cm2_basic', '0.3.0', '72', None, 'x86_64'))
    pkgName = 'ha3_runtime-debuginfo-1.9.0-nightly_201404221447.x86_64'
    assert(splitPkgName3(pkgName) == ('ha3_runtime-debuginfo', '1.9.0', 'nightly_201404221447', None, 'x86_64'))
    pkgName = 'apsara-sdk-0.10.1-rc_3.x86_64'
    assert(splitPkgName3(pkgName) == ('apsara-sdk', '0.10.1', 'rc_3', None, 'x86_64'))
    pkgName = 'mxml-2.6-1.x86_64'
    assert(splitPkgName3(pkgName) == ('mxml', '2.6', '1', None, 'x86_64'))
    pkgName = 'snappy-devel-1.0.5-1.x86_64'
    assert(splitPkgName3(pkgName) == ('snappy-devel', '1.0.5', '1', None, 'x86_64'))
    pkgName = 'zookeeper-client-3.3.5-rc_4.x86_64'
    assert(splitPkgName3(pkgName) == ('zookeeper-client', '3.3.5', 'rc_4', None, 'x86_64'))
    pkgName = 'kvtracer-0.0.1-nightly_201404031618.x86_64'
    assert(splitPkgName3(pkgName) == ('kvtracer', '0.0.1', 'nightly_201404031618', None, 'x86_64'))
    pkgName = 'libunwind-0.99-0.x86_64'
    assert(splitPkgName3(pkgName) == ('libunwind', '0.99', '0', None, 'x86_64'))
    pkgName = 'deploy_express-tools-0.10.0-rc_6.x86_64'
    assert(splitPkgName3(pkgName) == ('deploy_express-tools', '0.10.0', 'rc_6', None, 'x86_64'))
    pkgName = 'local_agent-0.7.1-rc_4.x86_64'
    assert(splitPkgName3(pkgName) == ('local_agent', '0.7.1', 'rc_4', None, 'x86_64'))
    pkgName = 'arpc-0.14.2-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('arpc', '0.14.2', 'rc_1', None, 'x86_64'))
    pkgName = 'swift-0.8.0-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('swift', '0.8.0', 'rc_1', None, 'x86_64'))
    pkgName = 'fslib-devel-0.6.10-rc_3.x86_64'
    assert(splitPkgName3(pkgName) == ('fslib-devel', '0.6.10', 'rc_3', None, 'x86_64'))
    pkgName = 'kvtracer-devel-0.0.1-nightly_201404031618.x86_64'
    assert(splitPkgName3(pkgName) == ('kvtracer-devel', '0.0.1', 'nightly_201404031618', None, 'x86_64'))
    pkgName = 'amonitor-0.1.6-rc_4.x86_64'
    assert(splitPkgName3(pkgName) == ('amonitor', '0.1.6', 'rc_4', None, 'x86_64'))
    pkgName = 'swift-devel-0.8.0-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('swift-devel', '0.8.0', 'rc_1', None, 'x86_64'))
    pkgName = 't_search_cm2_server_proto-0.3.0-77.x86_64'
    assert(splitPkgName3(pkgName) == ('t_search_cm2_server_proto', '0.3.0', '77', None, 'x86_64'))
    pkgName = 't_search_cm2_hb_node-0.3.0-66.x86_64'
    assert(splitPkgName3(pkgName) == ('t_search_cm2_hb_node', '0.3.0', '66', None, 'x86_64'))
    pkgName = 'ha3_runtime-devel-1.9.0-nightly_201404221447.x86_64'
    assert(splitPkgName3(pkgName) == ('ha3_runtime-devel', '1.9.0', 'nightly_201404221447', None, 'x86_64'))
    pkgName = 'python-2.4.3-27.el5.x86_64'
    assert(splitPkgName3(pkgName) == ('python', '2.4.3', '27.el5', None, 'x86_64'))
    pkgName = 'ha3_runtime-1.9.0-nightly_201404221447.x86_64'
    assert(splitPkgName3(pkgName) == ('ha3_runtime', '1.9.0', 'nightly_201404221447', None, 'x86_64'))
    pkgName = 'local_agent-devel-0.7.1-rc_4.x86_64'
    assert(splitPkgName3(pkgName) == ('local_agent-devel', '0.7.1', 'rc_4', None, 'x86_64'))
    pkgName = 'autil-0.6.12-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('autil', '0.6.12', 'rc_1', None, 'x86_64'))
    pkgName = 'indexlib-1.9.0-nightly_201404221445.x86_64'
    assert(splitPkgName3(pkgName) == ('indexlib', '1.9.0', 'nightly_201404221445', None, 'x86_64'))
    pkgName = 'zookeeper-client-devel-3.3.5-rc_4.x86_64'
    assert(splitPkgName3(pkgName) == ('zookeeper-client-devel', '3.3.5', 'rc_4', None, 'x86_64'))
    pkgName = 'anet-1.3.3-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('anet', '1.3.3', 'rc_1', None, 'x86_64'))
    pkgName = 'amonitor-devel-0.1.6-rc_4.x86_64'
    assert(splitPkgName3(pkgName) == ('amonitor-devel', '0.1.6', 'rc_4', None, 'x86_64'))
    pkgName = 'ha3_runtime-tools-1.9.0-nightly_201404221447.x86_64'
    assert(splitPkgName3(pkgName) == ('ha3_runtime-tools', '1.9.0', 'nightly_201404221447', None, 'x86_64'))
    pkgName = 'python-protobuf-2.4.2-rc_2.x86_64'
    assert(splitPkgName3(pkgName) == ('python-protobuf', '2.4.2', 'rc_2', None, 'x86_64'))
    pkgName = 'indexlib-devel-1.9.0-nightly_201404221445.x86_64'
    assert(splitPkgName3(pkgName) == ('indexlib-devel', '1.9.0', 'nightly_201404221445', None, 'x86_64'))
    pkgName = 'apsara_tools-0.10.1-0.x86_64'
    assert(splitPkgName3(pkgName) == ('apsara_tools', '0.10.1', '0', None, 'x86_64'))
    pkgName = 'deploy_express-devel-0.10.0-rc_6.x86_64'
    assert(splitPkgName3(pkgName) == ('deploy_express-devel', '0.10.0', 'rc_6', None, 'x86_64'))
    pkgName = 'libhdfs-cdh-devel-2.0.2-0.x86_64'
    assert(splitPkgName3(pkgName) == ('libhdfs-cdh-devel', '2.0.2', '0', None, 'x86_64'))
    pkgName = 'autil-devel-0.6.12-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('autil-devel', '0.6.12', 'rc_1', None, 'x86_64'))
    pkgName = 'protobuf-2.4.2-rc_2.x86_64'
    assert(splitPkgName3(pkgName) == ('protobuf', '2.4.2', 'rc_2', None, 'x86_64'))
    pkgName = 't_search_cm2_server_pyproto-0.3.0-77.x86_64'
    assert(splitPkgName3(pkgName) == ('t_search_cm2_server_pyproto', '0.3.0', '77', None, 'x86_64'))
    pkgName = 'arpc-devel-0.14.2-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('arpc-devel', '0.14.2', 'rc_1', None, 'x86_64'))
    pkgName = 'swift-tools-0.8.0-rc_1.x86_64'
    assert(splitPkgName3(pkgName) == ('swift-tools', '0.8.0', 'rc_1', None, 'x86_64'))
    pkgName = 't_search_cm2_basic_pyproto-0.3.0-72.x86_64'
    assert(splitPkgName3(pkgName) == ('t_search_cm2_basic_pyproto', '0.3.0', '72', None, 'x86_64'))
    pkgName = 'copper-1.0.4'
    assert(splitPkgName3(pkgName) == ('copper', '1.0.4', None, None, None))
    pkgName = 'copper-1.0.4-51.el5'
    assert(splitPkgName3(pkgName) == ('copper', '1.0.4', '51.el5', None, None))
    pkgName = 'copper-1.0.4-51.el5.x86_64'
    assert(splitPkgName3(pkgName) == ('copper', '1.0.4', '51.el5', None, 'x86_64'))
    pkgName = 'copper-1.0.4-51.el5.noarch'
    assert(splitPkgName3(pkgName) == ('copper', '1.0.4', '51.el5', None, 'noarch'))
    pkgName = 'libxml2-2.6.26-2.1.12.el5_7.2.x86_64'
    assert(splitPkgName3(pkgName) == ('libxml2', '2.6.26', '2.1.12.el5_7.2', None, 'x86_64'))
    pkgName = 'libxml2-2.6.26-2.1.12.el5_7.2'
    assert(splitPkgName3(pkgName) == ('libxml2', '2.6.26', '2.1.12.el5_7.2', None, None))
    pkgName = 'openssl-devel-0.9.8e-22.el5.4.x86_64'
    assert(splitPkgName3(pkgName) == ('openssl-devel', '0.9.8e', '22.el5.4', None, 'x86_64'))
    pkgName = 'openssl-devel-0.9.8e-22.el5.4'
    assert(splitPkgName3(pkgName) == ('openssl-devel', '0.9.8e', '22.el5.4', None, None))
    pkgName = 'tzdata-2011g-1.el5.x86_64.rpm'
    assert(splitPkgName3(pkgName) == ('tzdata', '2011g', '1.el5', None, 'x86_64'))
    pkgName = 'binutils-2.17.50.0.6-14.el5.x86_64'
    assert(splitPkgName3(pkgName) == ('binutils', '2.17.50.0.6', '14.el5', None, 'x86_64'))



    
