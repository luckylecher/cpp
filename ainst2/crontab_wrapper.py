#! /usr/bin/python

import process
import file_util
from logger import Log
from tempfile import NamedTemporaryFile

class CrontabWrapper:
    def getCrontab(self, user=None, timeout=20):
        cmd = 'crontab -l'
        if user:
            cmd += ' -u %s' % user
        out, err, code = process.run(cmd, timeout)
        if code != 0:
            return None
        return out

    def setCrontabFile(self, crontabFile, user=None, timeout=20):
        if not crontabFile:
            return False
        cmd = 'crontab %s' % crontabFile
        if user:
            cmd += ' -u %s' % user
        out, err, code = process.run(cmd, timeout)
        if code != 0:
            Log.cout(Log.ERROR, 'Set crontab failed: %s' % err)
            return False
        return True

    def setCrontabString(self, crontabString, user=None, timeout=20):
        if crontabString is None:
            return self.removeCrontab(user, timeout)
        fd = NamedTemporaryFile(suffix='_crontab', prefix='ainst_',
                                dir='/tmp')
        if not file_util.writeToFp(fd, crontabString):
            return False
        return self.setCrontabFile(fd.name, user, timeout)

    def removeCrontab(self, user=None, timeout=20):
        cmd = 'crontab -r'
        if user:
            cmd += ' -u %s' % user
        out, err, code = process.run(cmd, timeout)
        if code != 0:
            return False
        return True

if __name__ == '__main__':
    wrapper = CrontabWrapper()
    crontab = wrapper.getCrontab()
    myCrontab = '0 0 1 * * ls\n'
    ret = wrapper.setCrontabString(myCrontab)
    print 'set', ret
    newCrontab = wrapper.getCrontab()
    print newCrontab
    if crontab is not None:
        wrapper.setCrontabString(crontab)
        print 'o get', wrapper.getCrontab()
    else:
        ret = wrapper.removeCrontab()
        print 'remove, ', ret

