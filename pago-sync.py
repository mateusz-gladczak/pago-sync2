#PAGO sync
import os
import scp
import paramiko
import logging
import functions as f
from scp import SCPClient

def main():
    print("PAGO-SYNC is running")
    username = f.readConfig("username")
    password = f.readConfig("password")
    server = f.readConfig("server")
    ftproot = f.readConfig("ftproot")
    localroot = f.readConfig("localroot")

    serverdirs = [
        '/production/input',
        '/production/output',
        '/production/outputpdf',
        '/test/input',
        '/test/output',
        '/test/outputpdf'
        ]
#region Start
    logging.basicConfig(filename = "ftpsync.log", level = logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logging.info("-------------------------------")
    logging.info("starting ssh session to " + server)
    logging.info("initial configuration: server:" + server + " username:" + username + " ftproot:" + ftproot + " localroot:" + localroot )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect (server, username = username, password = password)
    status = ssh.get_transport().is_active()
    logging.info("changing directory to " + ftproot)
    command = 'cd ' + ftproot

    logging.info("listing directory " + ftproot)
    clients = f.ssh_command(ssh, "ls " + ftproot)

    sourcefiles = {}
    localfiles = {}
#RegionEnd
    for client in clients:
        cli = client.rstrip("\n")
        #create mirrored directories
        for serverdir in serverdirs:
            logging.info(ftproot + cli + serverdir)
            if not os.path.exists(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir)):
                logging.info("path " + localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + " does not exists")
                os.makedirs(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir))
            sfiles = f.ssh_command(ssh, "ls " + ftproot + cli + serverdir)
            #proba usunięcia newline
            sfiles = list(map(str.strip, sfiles))
            #check if directory is input or output
            #input - transfer server -> client
#Region Server INPUT
            if "input" in serverdir: 
                sTree = f.ssh_command(ssh, "python /home/pago-ftp/tree.py " + ftproot + cli + serverdir) #pobieranie struktury katalogu input
                for sfile in sfiles: #! zamiast tego będize iterowanie po liście
                #!tutaj musi być iteracja po katalogach i podkatalogach - zrobić słownik i iterować po słowniku
                
                    md5 = f.ssh_md5sum(ssh, ftproot + cli + serverdir + "/" + sfile)
                #add to filename:md5 dictionary
                    sourcefiles[serverdir + "/" + sfile] = md5
                #transfer
                    scp = SCPClient(ssh.get_transport())
                    logging.info("server >>> client : " + sfile)
                    scp.get(ftproot + cli + serverdir + "/" + sfile, localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + "\\" + sfile)
                    if f.verifyDownloadFileTransfer(sourcefiles[serverdir + "/" + sfile], localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + "\\" + sfile):
                        logging.info(ftproot + cli + serverdir + "/" + sfile + " transfer OK | MD5: " + sourcefiles[serverdir + "/" + sfile])
                        logging.info("removing file: " + ftproot + cli + serverdir + "/" + sfile)
                        f.ssh_command(ssh, "rm " + ftproot + cli + serverdir + "/" + sfile.replace(" ", "\ "))
                    else:
                        logging.info(ftproot + cli + serverdir + "/" + sfile + " transfer FAILED")
#EndRegion
#Region Server OUTPUT
            #transfer client -> server
            elif "output" in serverdir:
                #files from server side in output
                logging.info(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir))
                lfiles = os.listdir(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir))
                for lfile in lfiles:
                    md5 = f.md5(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + "\\" + lfile)
                    #print (lfile+ " " + md5)
                    #MD5 Table
                    localfiles[f.serverPathToWindowsPath(serverdir) + "\\" + lfile] = md5
                    scp = SCPClient(ssh.get_transport())
                    logging.info("server <<< client: " + lfile)
                    localfile = localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + "\\" + lfile
                    remotefile = ftproot + cli + serverdir + "/" + lfile
                    scp.put(localfile, remotefile)
                    localmd5 = localfiles[f.serverPathToWindowsPath(serverdir) + "\\" + lfile]
                    remotemd5 = f.ssh_md5sum(ssh, ftproot + cli + serverdir + "/" + lfile)
                    if f.verifyUploadFileTransfer(localmd5, remotemd5):
                        logging.info(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + "\\" + lfile + " transfer OK | MD5: " + localfiles[f.serverPathToWindowsPath(serverdir) + "\\" + lfile])
                        logging.info("removing " + localfile)
                        os.remove(localfile)
                    else: 
                        logging.info(localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir) + "\\" + lfile + " transfer FAILED")
#EndRegion
                #directory syncing

                #filesToDelete = f.diffDir(sfiles, lfiles)

                #if len(filesToDelete)>0:
                #    for fileToDelete in filesToDelete:
                #        logging.info("removing " + ftproot + cli + serverdir + "/" + fileToDelete)
                #        f.ssh_command(ssh, "rm " + ftproot + cli + serverdir + "/" + fileToDelete.replace(" ", "\ "))

    logging.info("closing ssh connection")
    ssh.close

if __name__ == "__main__":
    main()