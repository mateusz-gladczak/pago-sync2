import pysftp
def sync_server_remote_to_local(username, password, server, remotedir, localdir):
    with pysftp.Connection(server, username, password) as sftp:
        sftp.get_r(remotedir, localdir)
        sftp.close()
sync_server_remote_to_local(username = "mateusz", password = "SuperNusia1991", server = "10.0.10.50", remotedir = "/ftproot/clients/testuser2/test/input", localdir = "E:\\ftproot\\dupa")
