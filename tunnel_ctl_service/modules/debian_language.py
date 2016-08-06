#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import tunnel_ctl_service.linode_util as linode_util
import paramiko

log = logging.getLogger("module:" + __name__)

# ssh commands
# languages
is_php5_installed = "dpkg-query -f '${Status} @@ ${binary:Package}\n' -W | grep -v '^deinstall ok config-files @@ ' | grep '^.* @@ php7.0$' > /dev/null"
install_php5 = "DEBIAN_FRONTEND=noninteractive apt-get install -y php7.0"
uninstall_php5 = "DEBIAN_FRONTEND=noninteractive apt-get remove -y php7.0"

def install_language(d):
    language = d.installation.language if d.installation else None
    if language == None:
        # removing all languages
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # removing php5
        if exec_ssh_rc(ssh, is_php5_installed) == 0:
            # php5 is installed
            log.info("linode %i: uninstalling PHP5 language" % d.linode_id)
            exec_ssh_rc(ssh, uninstall_php5)
        else:
            log.info("linode %i: PHP5 language is not installed, cannot remove" % d.linode_id)
        ssh.close()
    elif language == "php5":
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(d.ip_address, username = "root", password = d.server.login.password)
        # getting installation info
        if exec_ssh_rc(ssh, is_php5_installed) != 0:
            # no php5 installed
            log.info("linode %i: installing PHP5 language" % d.linode_id)
            exec_ssh_rc(ssh, install_php5)
        else:
            log.info("linode %i: PHP5 language is already installed" % d.linode_id)
        ssh.close()
    else:
        raise RuntimeError("unsupported language: %s, cannot handle" % language)

def handle_path_change(config, key, old_value, new_value):
    install_language(config)

linode_util.register_path_change("installation.language", handle_path_change)

def exec_ssh_rc(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.channel.recv_exit_status()
