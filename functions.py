#functions
def readConfig(keyname):
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    configVal = config['DEFAULT'][keyname]
    return(configVal)


def ssh_command(ssh, command):
    import paramiko
    cmd = command
    ssh.invoke_shell()
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return(stdout.readlines())

def ssh_md5sum(ssh, filename):
    import paramiko
    md5Command = "md5sum " + filename.replace(" ","\ ")
    ssh.invoke_shell()
    stdin, stdout, stderr = ssh.exec_command(md5Command)
    calcVal = stdout.readlines()
    #print(calcVal)
    a = str(calcVal[0]).split(" ")
    #a = (calcVal[0])
    #a = str(a)
    #a = a.split(" ")
    return(a[0])

def convertToWindowsPath(path):
    import re
    windowspath = re.escape(path)
    return windowspath

def serverPathToWindowsPath(path):
    return path.replace('/','\\')

def md5(fname):
    import hashlib
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verifyDownloadFileTransfer(sourcefileMD5, targetfile):
    if sourcefileMD5 == md5(targetfile):
        return True
    else:
        return False

def verifyUploadFileTransfer(sourceMD5, destMD5):
    if sourceMD5 == destMD5:
        return True
    else:
        return False

def diffDir(serverdir, localdir):
    #return (list(set(serverdir) - set(localdir)))
    rlist = [item for item in serverdir if item not in localdir]
    return rlist

def dirTree(serverdir):
    import os
    import sys
    for path, dirs, files in os.walk(sys.argv[1]):
        print (path)
        for f in files:
            print (f)


def sync_server_remote_to_local(username, password, server, remotedir, localdir):
    import pysftp
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=server, username = username, password = password, cnopts = cnopts) as sftp:
    #with pysftp.Connection(server, username, password,cnopts=cnopts) as sftp:
        #sftp.get_r(remotedir, localdir)
        get_r_portable(sftp, remotedir, localdir, preserve_mtime=False)
        sftp.close()

def sync_server_local_to_remote(username, password, server, remotedir, localdir):
    import pysftp
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=server, username = username, password = password, cnopts = cnopts) as sftp:
    #with pysftp.Connection(server, username, password,cnopts=cnopts) as sftp:
        #sftp.get_r(remotedir, localdir)
        put_r_portable(sftp, remotedir, localdir, preserve_mtime=False)
        sftp.close()



def get_r_portable(sftp, remotedir, localdir, preserve_mtime=False):
    import os
    from stat import S_IMODE, S_ISDIR, S_ISREG
    for entry in sftp.listdir(remotedir):
        remotepath = remotedir + "/" + entry
        localpath = os.path.join(localdir, entry)
        mode = sftp.stat(remotepath).st_mode
        if S_ISDIR(mode):
            try:
                os.mkdir(localpath)
            except OSError:     # dir exists
                pass
            get_r_portable(sftp, remotepath, localpath, preserve_mtime)
        elif S_ISREG(mode):
            sftp.get(remotepath, localpath, preserve_mtime=preserve_mtime)

def put_r_portable(sftp, remotedir, localdir, preserve_mtime=False):
    import os
    from stat import S_IMODE, S_ISDIR, S_ISREG
    for entry in os.listdir(localdir):
        remotepath = remotedir + "/" + entry
        print("remotepath - put_r_portable: " + remotepath)
        localpath = os.path.join(localdir, entry)
        print("localpath - put_r_portable: " + localpath)
        mode = os.stat(localpath).st_mode
        if S_ISDIR(mode):
            try:
                print("trying to create " + remotepath)
                sftp.mkdir(remotepath)
            except OSError:     # dir exists
                pass
            put_r_portable(sftp, remotepath, localpath, preserve_mtime)
        elif S_ISREG(mode):
            sftp.put(localpath, remotepath, preserve_mtime=preserve_mtime)