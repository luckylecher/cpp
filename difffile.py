import os,sys,re
import commands

class DiffFile:
    def __init__(self):
        self.FILE_TYPE_LIST = ["json", "cfg", "py", "h", "conf", "config"]
        self.TMP_FILE_NAME = ".diffflies0"
        self.PATH_MAP = {}
    
    #get file list in local dir
    def getFileList(self, dirPath):
        if self.isRemoteFile(dirPath):
            self.getRemoteFileList(dirPath)
            dirPath = self.PATH_MAP[dirPath]
        tmp = os.listdir(dirPath)
        flist = []
        for item in tmp:
            absPath = os.path.join(dirPath, item)
            fileSuffix = os.path.split(absPath)[1]
            fileType = fileSuffix[fileSuffix.rfind(".") + 1:]
            if os.path.isfile(absPath) and fileType in self.FILE_TYPE_LIST:
                flist.append(item)
        return flist

    #get config file from remote machine to local.
    def getRemoteFileList(self, remoteFilePath):
        colonPosition = remoteFilePath.find(":")
        server = remoteFilePath[:colonPosition]
        path = remoteFilePath[colonPosition + 1:]
        s, o = commands.getstatusoutput("ssh %s \"ls %s\"" % (server, path))
        if s > 0 :
            print o
            return None
        commands.getstatusoutput("rm -rf %s" % self.TMP_FILE_NAME)
        commands.getstatusoutput("mkdir %s" % self.TMP_FILE_NAME)
        for item in o.split("\n"):
            self.getRemoteFile(os.path.join(remoteFilePath, item), self.TMP_FILE_NAME)
        self.PATH_MAP[remoteFilePath] = self.TMP_FILE_NAME
        self.TMP_FILE_NAME = self.TMP_FILE_NAME.replace("0", "1")

    def getFileMd5(self, fpath, fname):
        cmd = "md5sum %s | awk '{print $1}'" % os.path.join(fpath, fname)
        s, o = commands.getstatusoutput(cmd)
        if s > 0:
            return ""
        return o

    def output(self, data, key):    
        print "================ [%14s] ===============" % key
        for item in data[key]:
            print item

    def isRemoteFile(self, path):
        ptn = re.compile(r"(^.*?@.*?\:.*$)")
        tmp = ptn.findall(path)
        if len(tmp) > 0:
            return True
        return False

    def getRemoteFile(self, fpath, localDir):
        cmd = "scp %s %s" % (fpath, localDir)
        s, o = commands.getstatusoutput(cmd)
        if s > 0:
            print o
            return False
        return True

    def startUp(self, sourcePath, destPath):
        data = {}
        self.PATH_MAP[sourcePath] = sourcePath
        self.PATH_MAP[destPath] = destPath
        sflist = self.getFileList(sourcePath)
        dflist = self.getFileList(destPath)
        data["Deleted file"] = []
        data["Unchanged file"] = []
        data["Changed file"] = []
        data["New file"] = []
        for item in sflist:
            if item not in dflist:
                data["Deleted file"].append( os.path.join(sourcePath, item) )
                continue
            if self.getFileMd5(self.PATH_MAP[sourcePath], item) == self.getFileMd5(self.PATH_MAP[destPath], item):
                data["Unchanged file"].append(item + "\t")
            else:
                data["Changed file"].append("vimdiff %s %s" % (os.path.join(self.PATH_MAP[sourcePath], item), os.path.join(PATH[destPath], item)))
        for item in dflist:
            if item not in sflist:
                data["New file"].append(os.path.join(destPath, item))
        self.output(data, "Deleted file")
        self.output(data, "New file")    
        self.output(data, "Unchanged file")    
        print "================ [%14s] ===============" % "Changed file"
        print "Path map:"
        if self.isRemoteFile(sourcePath):
            print "[%s] ==> [%s]" % (sourcePath, self.PATH_MAP[sourcePath])
        if self.isRemoteFile(destPath):
            print "[%s] ==> [%s]" % (destPath, self.PATH_MAP[destPath])
        print "&&".join(data["Changed file"])

if __name__ == "__main__":
    DiffFile().startUp(sys.argv[1], sys.argv[2])
