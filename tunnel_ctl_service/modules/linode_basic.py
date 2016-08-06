#!/usr/bin/python3
# -*- coding: utf-8 -*-

from dictlist_utils import dict_obj
import time, logging
import paramiko
from tunnel_ctl_service.linode_util import linode_config_file, get_api, register_path_change

log = logging.getLogger("module:" + __name__)

def handle_path_change(config, key, old_value, new_value):
    pass

avail_datacenters = list()
def get_datacenters():
    if not avail_datacenters:
        avail_datacenters.clear()
        avail_datacenters.extend(get_api().avail.datacenters())
    return avail_datacenters

avail_plans = list()
def get_plans():
    if not avail_plans:
        avail_plans.clear()
        avail_plans.extend(get_api().avail.linodeplans())
    return avail_plans

avail_distributions = list()
def get_distributions():
    if not avail_distributions:
        avail_distributions.clear()
        avail_distributions.extend(get_api().avail.distributions())
    return avail_distributions

avail_kernels = list()
def get_kernels():
    if not avail_kernels:
        avail_kernels.clear()
        avail_kernels.extend(get_api().avail.kernels())
    return avail_kernels

def pick_cheapest_plan(**kwargs):
    good_plans = []
    for plan in get_plans():
        good = True
        for k, v in kwargs.items():
            good = good and v(plan[k])
        if good:
            good_plans.append(plan)
    #
    if not good_plans: return None
    # now sorting plans by price
    good_plans.sort(key=lambda x: x["PRICE"])
    #
    return good_plans[0]["PLANID"]

def pick_distribution(name):
    for d in get_distributions():
        d = dict_obj(d)
        if d.LABEL == name: return d.DISTRIBUTIONID
    raise RuntimeError("distribution with such name is not found: %s" % name)

def pick_kernel():
    # returning 4.5.5-x86_64-linode69
    return 237 # TODO: adjust this

def allocate_linode(d):
    """
    Creates Linode, its disks, configuration and boots it up.
    """
    log.info("allocating Linode server")
    api = get_api()
    # allocating linode_id
    result = api.linode.create(
            PlanID = pick_cheapest_plan(RAM = lambda x: int(x) >= int(d.server.ram)),
            DatacenterID = get_datacenters()[0]["DATACENTERID"] # TODO: make this configurable
        )
    d.linode_id = result["LinodeID"]
    log.info("... allocated, linode id: %i" % d.linode_id)
    
    # allocating disks
    log.info("... allocating root disk")
    root_job = api.linode.disk.createfromdistribution(
            LinodeID = d.linode_id,
            Label = "ROOT",
            size = 2048, # MB, TODO: adjust this
            DistributionID = pick_distribution(d.server.distribution),
            rootPass = d.server.login.password, # TODO: add handling of weak password exceptions
        )
    root_job = dict_obj(root_job)
    wait_for_job(d.linode_id, root_job.JobID)
    log.info("... root allocated, disk id: %i" % root_job.DiskID)
    
    log.info("... allocating swap")
    swap_job = api.linode.disk.create(
            LinodeID = d.linode_id,
            Label = "SWAP",
            Type = "swap",
            size = 256, # MB, TODO: adjust this
        )
    swap_job = dict_obj(swap_job)
    wait_for_job(d.linode_id, swap_job.JobID)
    log.info("... swap allocated, disk id: %i" % swap_job.DiskID)
    
    # getting ip
    for ip_obj in api.linode.ip.list(LinodeId = d.linode_id):
        ip_obj = dict_obj(ip_obj)
        if ip_obj.ISPUBLIC:
            d.ip_address = ip_obj.IPADDRESS
            log.info("... ip address is: %s" % d.ip_address)
            break
    
    # creating config
    config_result = api.linode.config.create(
            LinodeID = d.linode_id,
            Label = "default",
            DiskList = "%i,%i" % (root_job.DiskID, swap_job.DiskID),
            helper_distro = True,
            devtmpfs_automount = True,
            helper_network = True,
            RootDeviceRO = True,
            RAMLimit = 0,
            KernelID = pick_kernel(),
            Comments = "A default configuration containing root & swap disks, includes helper and no ram limitations",
        )
    config_id = config_result["ConfigID"]
    
    # booting
    log.info("... booting up")
    boot_job = api.linode.boot(LinodeID = d.linode_id, ConfigID = config_id)
    boot_job = dict_obj(boot_job)
    wait_for_job(d.linode_id, boot_job.JobID)
    
    # fin!
    log.info("done: linode ID %i is booted now" % d.linode_id)
    return d.linode_id

def delete_linode(linode_id):
    log.info("deleting Linode server id %i" % linode_id)
    api = get_api()
    
    log.info("... shutting down")
    # shutting down first
    try:
        shutdown_job = api.linode.shutdown(LinodeID = linode_id)
        shutdown_job = dict_obj(shutdown_job)
        wait_for_job(linode_id, shutdown_job.JobID)
    except:
        pass
    
    # deleting all discs: deletion of Linode requires all disks to be deleted
    # HUGE TODO: make sure all data is saved to safe place!
    for disk_obj in api.linode.disk.list(LinodeID = linode_id):
        disk_obj = dict_obj(disk_obj)
        log.info("... deleting disk %i" % disk_obj.DISKID)
        del_job = api.linode.disk.delete(LinodeID = linode_id, DiskID = disk_obj.DISKID)
        del_job = dict_obj(del_job)
        wait_for_job(linode_id, del_job.JobID)
    
    # now deleting linode itself
    log.info("... deleting linode itself %i" % linode_id)
    api.linode.delete(LinodeID = linode_id)

def setup_password(d):
    # setting up user
    log.info("account setup: opening SSH connection")
    username = d.server.login.username
    password = d.server.login.password
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(d.ip_address, username = "root", password = password)
    log.info("linode %i: adding user %s" % (d.linode_id, username))
    exec_ssh_rc(ssh, "useradd -m -s /bin/bash %s" % username)
    stdin, stdout, stderr = ssh.exec_command("passwd %s" % username)
    stdin.write(password + "\n" + password + "\n")
    stdin.close()
    if stdout.channel.recv_exit_status() != 0:
        log.warn("failed to set up password for user %s, you can do this manually from root" % username)
    ssh.close()

def full_install(d):
    # installing other components
    # TODO
    #install_server(d)
    #install_database(d)
    #install_framework(d)
    #install_language(d)
    # TODO: full install
    pass

#    def refresh_status(self):
#        if not self.server.login:
#            raise RuntimeError("no credentials for linode instance %i, can't manage" % self.linode_id)
#        # getting instance
#        api = get_api()
#        linode_instances = api.linode.list(LinodeID=self.linode_id)
#        if not linode_instances:
#            raise RuntimeError("linode instance %i doesn't exists" % self.linode_id)
#        if len(linode_instances) > 1:
#            raise RuntimeError("linode api returned more than 1 instance for concrete linode id %i" % self.linode_id)
#        linode_instance = dict_obj(linode_instances[0])
#        # setting params
#        self.server.cloud = "Linode"
#        self.server.ram = linode_instance.TOTALRAM
#         # getting ip
#         ip_list = api.linode.ip.list(LinodeID=li.LINODEID)
#         if not ip_list:
#             log.warn("instance %i has no IPs, unable to obtain full information" % li.LINODEID)
#         else:
#             # getting SSH access
#             ssh = paramiko.SSHClient()
#             ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#             ssh.connect('semplar.net', **self.server.login)
#             # getting installation info
#             inst = self.installation
#             if exec_ssh_rc(ssh, is_apache_installed):
#                 pass

def wait_for_job(linode_id, job_id, period = 5):
    api = get_api()
    while True:
        pending_jobs = api.linode.job.list(LinodeID = linode_id, JobID = job_id, pendingOnly = 1)
        if not pending_jobs: break
        time.sleep(period)

def get_status():
    api = get_api()
    return map(lambda x: linode_config_file(x["LINODEID"]), api.linode.list())

register_path_change("server", handle_path_change)

def exec_ssh_rc(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.channel.recv_exit_status()

