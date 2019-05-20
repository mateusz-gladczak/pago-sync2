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
    logPath = "."
    fileName = "ftpsync"

    serverdirs = [
        '/production/input',
        '/production/output',
        '/production/outputpdf',
        '/test/input',
        '/test/output',
        '/test/outputpdf'
        ]
#region Start
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
        logging.StreamHandler()
    ])
    logging.info("-------------------------------")
    logging.info("starting ssh session to " + server)
    logging.info("initial configuration: server:" + server + " username:" + username + " ftproot:" + ftproot + " localroot:" + localroot )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
            serverfolder = ftproot + cli + serverdir
            localfolder = localroot + "\\" + cli + f.serverPathToWindowsPath(serverdir)
            logging.info(serverfolder)
            if not os.path.exists(localfolder):
                logging.info("path " + localfolder + " does not exist, creating")
                os.makedirs(localfolder)
#Region Server INPUT
            if "input" in serverdir:
                f.sync_server_remote_to_local(username = username, password = password, server = server, remotedir = serverfolder, localdir = localfolder)
#EndRegion
#Region Server OUTPUT
            #transfer client -> server
            elif "output" in serverdir:
                f.sync_server_local_to_remote(username = username, password = password, server = server, remotedir = serverfolder, localdir = localfolder)
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