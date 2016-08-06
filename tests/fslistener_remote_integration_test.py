#!/usr/bin/python3
# -*- coding: utf-8 -*-

import unittest
#
import time
import paramiko

from dictlist_utils import dict_obj
from watchdog.observers import Observer
from fslistener_remote_ssh import ConfigurationChangeHandler

ssh_client = None

def ssh_provider():
    try:
        stdin, stdout, stderr = ssh_client.exec_command("echo 1")
        assert stdout.readline().strip() == "1"
    except:
        try: ssh_client.close()
        except: pass
        ssh_client = open_ssh()
    return ssh_client

def open_ssh():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect('semplar.net', username='testuser', password='testpass_xMVdPP@~')
    return ssh_client

class LocalFSListenerTest(unittest.TestCase):
    
    callback = None
    fslistener = None
    tmpdir = None
    actions = None
    ssh_modifyconn = None
    
    def setUp(self):
        # creating empty callback
        cb = self.callback = dict_obj()
        sa = self.actions = list()
        cb.rename_config = lambda oldname, newname: sa.append(('r', oldname, newname))
        cb.update_config = lambda cname, json: sa.append(('u', cname, json))
        cb.save_config = lambda cname: sa.append(('s', cname,))
        cb.delete_config = lambda cname: sa.append(('d', cname,))
        # ssh_client for changes
        self.ssh_modifyconn = open_ssh()
        # creating tmpdir
        td = self.tmpdir = "pyunittest_fslistener/testrun_%s" % time.time()
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('mkdir -p "%s"' % self.tmpdir)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to create test directory")
        # creating fslistener
        fl = self.fslistener = ConfigurationChangeHandler(cb, td, ssh_provider)
        fl.start()
    
    def test_move(self):
        print ("Testing onMove()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        # creating file
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('echo "{}" > "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to create test file")
        # preparing
        sa = self.actions
        time.sleep(5)
        sa.clear()
        # acting
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('mv "%s" "%s"' % (fulln, fulln + ".rename"))
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to move test file")
        # checking
        time.sleep(5)
        self.assertIn(('r', fn, fn + ".rename"), sa, "expected action list has rename")
        # uninit
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('rm "%s"' % (fulln + ".rename"))
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to remove test file")
    
    def test_create(self):
        print ("Testing onCreate()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        # preparing
        sa = self.actions
        time.sleep(5)
        sa.clear()
        # acting
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('echo "{}" > "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to create test file")
        # checking
        time.sleep(5)
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('test -f "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to make sure test file exists")
        self.assertIn(('u', fn, {}), sa, "expected new file action")
        # uninit
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('rm "%s"' % (fulln))
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to remove test file")
    
    def test_delete(self):
        print ("Testing onDelete()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('test -e "%s"' % fulln)
        self.assertNotEqual(0, stdout.channel.recv_exit_status(), "file is already there, refusing to remove it")
        # preparing
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('echo "{}" > "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to create test file")
        sa = self.actions
        time.sleep(5)
        sa.clear()
        # acting
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('rm "%s"' % (fulln))
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to remove test file")
        # checking
        time.sleep(5)
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('test -e "%s"' % fulln)
        self.assertNotEqual(0, stdout.channel.recv_exit_status(), "file was not deleted")
        self.assertIn(('d', fn), sa, "expected new file action")
        # uninit
        pass
    
    def test_modify(self):
        print ("Testing onModify()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('test -e "%s"' % fulln)
        self.assertNotEqual(0, stdout.channel.recv_exit_status(), "file is already there, refusing to remove it")
        # preparing
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('echo -n "" > "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to create test file")
        sa = self.actions
        time.sleep(5)
        sa.clear()
        # acting
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('echo "{\\"abraka\\":\\"dabra\\"}" >> "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to modify test file")
        # checking
        time.sleep(5)
        self.assertIn(('u', fn, {"abraka":"dabra"}), sa, "expected new file action")
        # uninit
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('rm "%s"' % fulln)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to remove test file")
    
    def tearDown(self):
        # removing fslistener
        self.fslistener.stop()
        self.fslistener = None
        # removing tmpdir
        stdin, stdout, stderr = self.ssh_modifyconn.exec_command('rmdir "%s"' % self.tmpdir)
        self.assertEqual(0, stdout.channel.recv_exit_status(), "failed to remove test directory")
        # closing ssh
        try: self.ssh_modifyconn.close()
        except: pass
