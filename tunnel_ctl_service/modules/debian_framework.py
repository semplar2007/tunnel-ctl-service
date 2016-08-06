#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import tunnel_ctl_service.linode_util as linode_util
import paramiko

log = logging.getLogger("module:" + __name__)

# ssh commands
# frameworks
is_wordpress_installed = "dpkg-query -f '${Status} @@ ${binary:Package}\n' -W | grep -v '^deinstall ok config-files @@ ' | grep '^.* @@ wordpress$' > /dev/null"
install_wordpress = "DEBIAN_FRONTEND=noninteractive apt-get install -y wordpress"
uninstall_wordpress = "DEBIAN_FRONTEND=noninteractive apt-get remove -y wordpress"

def install_framework(d):
    framework = d.installation.framework if d.installation else None
    if framework == None:
        # removing all frameworks
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_wordpress_installed) == 0:
            # wordpress is installed
            log.info("linode %i: uninstalling Wordpress framework" % d.linode_id)
            exec_ssh_rc(ssh, uninstall_wordpress)
        else:
            log.info("linode %i: Wordpress is not installed, cannot remove" % d.linode_id)
        ssh.close()
    elif framework.name == "wordpress":
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_wordpress_installed) != 0:
            # no wordpress installed
            log.info("linode %i: installing Wordpress framework" % d.linode_id)
            exec_ssh_rc(ssh, install_wordpress)
        else:
            log.info("linode %i: Wordpress is already installed" % d.linode_id)
        ssh.close()
    else:
        raise RuntimeError("unsupported framework: %s, cannot handle" % framework.name)

def handle_path_change(config, key, old_value, new_value):
    install_framework(config)

linode_util.register_path_change("installation.framework", handle_path_change)

def exec_ssh_rc(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.channel.recv_exit_status()
