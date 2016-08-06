#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, traceback
# remote service libs
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
#
import logging, json

log = logging.getLogger("fslistener")

class ConfigurationChangeHandler(FileSystemEventHandler):
    
    callback = None
    config_dir = None
    observer = None
    
    def __init__(self, callback, config_dir):
        if not callback: raise ValueError("callback is not specified!")
        if not config_dir: raise ValueError("config_dir is expected to be specified")
        self.config_dir = config_dir
        self.callback = callback
        # local observer
        obs = self.observer = Observer()
        event_handler = ConfigurationChangeHandler(callback)
        obs.schedule(event_handler, path = config_dir, recursive = False)
        obs.start()
    
    def join(self):
        self.observer.join()
    
    def on_moved(self, event):
        if os.path.isdir(event.src_path):
            return
        log.debug("FS change: file moved: %s" % event)
        fdir, fname = os.path.split(event.src_path)
        newdir, newname = os.path.split(event.dest_path)
        #
        if fname.startswith(".") and newname.startswith(".") or fdir != self.config_dir and newdir != self.config_dir:
            log.debug("FS change: ... ignoring hidden file %s" % newname)
            return
        # file was moved out outside of folder, or moved inside
        if not fname.startswith(".") and fdir == self.config_dir and (newname.startswith(".") or newdir != self.config_dir):
            log.info("... deleted file: %s" % fname)
            self.on_deleted(event, event.src_path)
        elif (fname.startswith(".") or fdir != self.config_dir) and not newname.startswith(".") and newdir == self.config_dir:
            log.info("... loading new file: %s" % fname)
            self.on_created(event, event.dest_path)
        elif not fname.startswith(".") and fdir == self.config_dir and not newname.startswith(".") and newdir == self.config_dir:
            # same dir, file was just renamed
            try: self.callback.rename_config(fname, newname)
            except Exception: traceback.print_exc()
    
    def on_created(self, event, path = None):
        if path is None: path = event.src_path
        if os.path.isdir(path):
            return
        log.debug("FS change: file created: %s" % event)
        fname = os.path.split(path)[1]
        if fname.startswith("."):
            log.debug("FS change: ... ignoring hidden file %s" % fname)
            return
        try:
            with open(self.config_dir + '/' + fname, "r") as fp:
                log.info("... reloading file: %s" % fname)
                self.callback.update_config(fname, json.load(fp))
                self.callback.save_config(fname)
        except Exception:
            traceback.print_exc()
    
    def on_deleted(self, event, path = None):
        if path is None: path = event.src_path
        if os.path.isdir(path):
            return
        log.debug("FS change: file deleted: %s" % event)
        fname = os.path.split(path)[1]
        if fname.startswith("."):
            log.debug("FS change: ... ignoring hidden file %s" % fname)
            return
        try:
            self.callback.delete_config(fname)
        except Exception:
            traceback.print_exc()
    
    def on_modified(self, event):
        if os.path.isdir(event.src_path):
            return
        log.debug("FS change: file modified: %s" % event)
        fname = os.path.split(event.src_path)[1]
        if fname.startswith("."):
            log.debug("FS change: ... ignoring hidden file %s" % fname)
            return
        if not os.path.exists(self.config_dir + '/' + fname):
            log.debug("FS change: actually, file is deleted now %s" % fname)
            try:
                log.info("... deleted file: %s" % fname)
                self.callback.delete_config(fname)
            except Exception:
                traceback.print_exc()
            return
        with open(self.config_dir + '/' + fname, "r") as fp:
            try:
                log.info("... reloading file: %s" % fname)
                self.callback.update_config(fname, json.load(fp))
                self.callback.save_config(fname)
            except Exception:
                traceback.print_exc()
    
    def isdir(self, path):
        return os.path.isdir(path)
    
    def isfile(self, path):
        return os.path.isfile(path)
    
    def exists(self, path):
        return os.path.exists(path)
    
    def readfile(self, path):
        with open(path, "r") as fp:
            return "\n".join(fp.readlines())
    
    def writefile(self, path, data):
        with open(path, "w") as fp:
            fp.write(data)
    
    def unlink(self, path):
        os.unlink(path)
    
    def mkdir(self, path):
        os.mkdir(path)
    
    def rmdir(self, path):
        os.rmdir(path)
    
    def listdir(self, path):
        return os.listdir(path)
    
    def rename(self, src, dst):
        return os.rename(src, dst)
