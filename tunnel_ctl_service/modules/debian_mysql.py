#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import tunnel_ctl_service.linode_util as linode_util
import paramiko

log = logging.getLogger("module:" + __name__)

# ssh commands
# databases
is_mysql_installed = "dpkg-query -f '${Status} @@ ${binary:Package}\n' -W | grep -v '^deinstall ok config-files @@ ' | grep '^.* @@ mysql-server$' > /dev/null"
install_mysql = "DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server"
uninstall_mysql = "DEBIAN_FRONTEND=noninteractive apt-get remove -y mysql-server"

def install_database(d):
    database = d.installation.database if d.installation else None
    if database == None:
        # removing all databases
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_mysql_installed) == 0:
            # mysql is installed
            log.info("linode %i: uninstalling MySQL server" % d.linode_id)
            exec_ssh_rc(ssh, uninstall_mysql)
        else:
            log.info("linode %i: MySQL server is not installed, cannot remove" % d.linode_id)
        ssh.close()
    elif database.provider == "mysql":
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_mysql_installed) != 0:
            # no mysql installed
            log.info("linode %i: installing MySQL server" % d.linode_id)
            exec_ssh_rc(ssh, install_mysql)
            # setting up root password
            exec_ssh_rc(ssh, "mysqladmin -u root password %s" % database.password)
        else:
            log.info("linode %i: MySQL server is already installed" % d.linode_id)
        ssh.close()
    else:
        raise RuntimeError("unsupported database: %s, cannot handle" % database.provider)

def handle_path_change(config, key, old_value, new_value):
    install_database(config)

linode_util.register_path_change("installation.database", handle_path_change)

def exec_ssh_rc(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.channel.recv_exit_status()

