#!/usr/bin/python3
# -*- coding: utf-8 -*-

import traceback
from os.path import split as path_split
# remote service libs
#
import logging, json
import threading

log = logging.getLogger("sshlistener")

class ConfigurationChangeHandler (threading.Thread):
    
    callback = None
    config_dir = None
    ssh_provider = None
    moves_stack = [ ]
    working = True
    
    def __init__(self, callback, config_dir, ssh_provider):
        super().__init__()
        if not callback: raise ValueError("callback is not specified!")
        if not config_dir: raise ValueError("config_dir is expected to be specified")
        self.config_dir = config_dir
        self.callback = callback
        self.ssh_provider = ssh_provider
    
    def run(self):
        while self.working:
            try:
                ssh_client = self.ssh_provider()
                stdin, stdout, stderr = ssh_client.exec_command('inotifywait -m "%s"' % self.config_dir)
                # inotifywait writes "Setting up watches." and "Watches established." to stdout, and actions themselves to stdin 
                while True:
                    l = stdout.readline()
                    ops_index = l.index(" ")
                    dirname = l[:ops_index]
                    file_index = l.index(" ", ops_index + 1)
                    actions = l[ops_index+1:file_index].split(",")
                    assert l[-1] == '\n'
                    filename = l[file_index+1:-1] # excluding trailing \n
                    for a in actions:
                        self.inotify_action(a, dirname, filename)
            except:
                traceback.print_exc()
    
    def stop(self):
        self.working = False
        try: self.ssh_provider.close()
        except: pass
    
    def inotify_action(self, action, dirname, filename):
        print ("inotify_action: %s: dir %s file %s" % (action, dirname, filename))
        if action == "DELETE":
            self.on_deleted(dirname + filename)
        elif action == "MODIFY":
            self.on_modified(dirname + filename)
        elif action == "CREATE":
            self.on_created(dirname + filename)
        elif action == "MOVED_FROM":
            # file is moved outside  dir
            # TODO
            pass
        elif action == "MOVED_TO":
            # file is moved inside dir
            # TODO
            pass
        else:
            # CLOSE_WRITE, CLOSE, ATTRIB aren't useful here
            pass
    
    def on_created(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -d "%s"' % path)
        if stdout.channel.recv_exit_status() == 0:
            return
        log.debug("FS change: file created: %s" % path)
        fname = path_split(path)[1]
        if fname.startswith("."):
            log.debug("FS change: ... ignoring hidden file %s" % fname)
            return
        try:
            stdin, stdout, stderr = self.ssh_provider().exec_command('cat "%s"' % (self.config_dir + '/' + fname))
            log.info("... reloading file: %s" % fname)
            self.callback.update_config(fname, json.loads("\n".join(stdout.readlines())))
            self.callback.save_config(fname)
        finally:
            try: stdin.close()
            except: pass
            try: stdout.close()
            except: pass
            try: stderr.close()
            except: pass
    
    def on_deleted(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -d "%s"' % path)
        if stdout.channel.recv_exit_status() == 0:
            return
        log.debug("FS change: file deleted: %s" % path)
        fname = path_split(path)[1]
        if fname.startswith("."):
            log.debug("FS change: ... ignoring hidden file %s" % fname)
            return
        try:
            self.callback.delete_config(fname)
        except Exception:
            traceback.print_exc()
    
    def on_modified(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -d "%s"' % path)
        if stdout.channel.recv_exit_status() == 0:
            return
        log.debug("FS change: file modified: %s" % path)
        fname = path_split(path)[1]
        if fname.startswith("."):
            log.debug("FS change: ... ignoring hidden file %s" % fname)
            return
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -e "%s"' % (self.config_dir + '/' + fname))
        if stdout.channel.recv_exit_status() != 0:
            log.debug("FS change: actually, file is deleted now %s" % fname)
            try:
                log.info("... deleted file: %s" % fname)
                self.callback.delete_config(fname)
            except Exception:
                traceback.print_exc()
            return
        try:
            stdin, stdout, stderr = self.ssh_provider().exec_command('cat "%s"' % (self.config_dir + '/' + fname))
            log.info("... reloading file: %s" % fname)
            self.callback.update_config(fname, json.loads("\n".join(stdout.readlines())))
            self.callback.save_config(fname)
        finally:
            try: stdin.close()
            except: pass
            try: stdout.close()
            except: pass
            try: stderr.close()
            except: pass
    
    def isdir(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -d "%s"' % path)
        return stdout.channel.recv_exit_status() == 0
    
    def isfile(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -f "%s"' % path)
        return stdout.channel.recv_exit_status() == 0
    
    def exists(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('test -e "%s"' % path)
        return stdout.channel.recv_exit_status() == 0
    
    def readfile(self, path):
        try:
            stdin, stdout, stderr = self.ssh_provider().exec_command('cat "%s"' % path)
            return "\n".join(stdout.readlines())
        finally:
            try: stdin.close()
            except: pass
            try: stdout.close()
            except: pass
            try: stderr.close()
            except: pass
    
    def writefile(self, path, data):
        try:
            stdin, stdout, stderr = self.ssh_provider().exec_command('cat > "%s"' % path)
            stdin.write(data)
        finally:
            try: stdin.close()
            except: pass
            try: stdout.close()
            except: pass
            try: stderr.close()
            except: pass
    
    def unlink(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('rm "%s"' % path)
        return stdout.channel.recv_exit_status() == 0
    
    def mkdir(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('mkdir "%s"' % path)
        return stdout.channel.recv_exit_status() == 0
    
    def rmdir(self, path):
        stdin, stdout, stderr = self.ssh_provider().exec_command('rmdir "%s"' % path)
        return stdout.channel.recv_exit_status() == 0
    
    def listdir(self, path):
        try:
            stdin, stdout, stderr = self.ssh_provider().exec_command('ls -Ap "%s"' % path)
            return stdout.readlines()
        finally:
            try: stdin.close()
            except: pass
            try: stdout.close()
            except: pass
            try: stderr.close()
            except: pass
    
    def rename(self, src, dst):
        stdin, stdout, stderr = self.ssh_provider().exec_command('mv "%s" "%s"' % (src, dst))
        return stdout.channel.recv_exit_status() == 0
