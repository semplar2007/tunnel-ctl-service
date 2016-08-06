#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import tunnel_ctl_service.linode_util as linode_util
import paramiko

log = logging.getLogger("module:" + __name__)

# ssh commands
# servers
is_apache_installed = "dpkg-query -f '${Status} @@ ${binary:Package}\n' -W | grep -v '^deinstall ok config-files @@ ' | grep '^.* @@ apache2$' > /dev/null"
install_apache = "DEBIAN_FRONTEND=noninteractive apt-get install -y apache2"
uninstall_apache = "DEBIAN_FRONTEND=noninteractive apt-get remove -y apache2"

def install_server(d):
    server = d.installation.server if d.installation else None
    if server == None:
        # removing apache web server
        # TODO: other removals may be needed here
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_apache_installed) == 0:
            # apache is installed, removing
            log.info("linode %i: uninstalling Apache" % d.linode_id)
            exec_ssh_rc(ssh, uninstall_apache)
        else:
            log.info("linode %i: Apache is not installed, cannot remove" % d.linode_id)
        ssh.close()
    elif server == "Apache":
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_apache_installed) != 0:
            # no apache installed
            log.info("linode %i: installing Apache" % d.linode_id)
            exec_ssh_rc(ssh, install_apache)
        else:
            log.info("linode %i: Apache is already installed" % d.linode_id)
        ssh.close()
    else:
        raise RuntimeError("unsupported server: %s, cannot handle" % server)

def handle_path_change(config, key, old_value, new_value):
    install_server(config)

linode_util.register_path_change("installation.server", handle_path_change)

def exec_ssh_rc(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.channel.recv_exit_status()

