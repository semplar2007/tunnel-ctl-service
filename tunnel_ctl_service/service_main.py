#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# python core libs
import sys, os, json
import logging.config, traceback
# components
from tunnel_ctl_service import service_model, linode_util
from dictlist_utils import dict_obj
#
from watchdog.observers import Observer
from tunnel_ctl_service.fslistener_local import ConfigurationChangeHandler

# configuration constants
SLEEP_PERIOD = 1.0 # seconds

log = logging.getLogger("main")
log.setLevel(logging.INFO)

global_config = dict_obj()
fs_listener = None

def load_global_config():
    conf_fn = "linode-service.conf"
    if os.path.exists(conf_fn):
        with open(conf_fn, "r") as f:
            conf = dict_obj(json.load(f))
    else:
        conf = dict_obj()
    return conf

def run_init():
    # configuring logging
    global_config = load_global_config()
    logging.config.dictConfig(global_config.log_dictconfig)
#     logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)
    # initializing observer
    callback = dict_obj()
    callback.rename_config = service_model.rename_config
    callback.update_config = service_model.update_config
    callback.save_config = service_model.save_config
    callback.delete_config = service_model.delete_config
    #
    fs_listener = ConfigurationChangeHandler(callback)
    # loading remembered configurations
    log.info("Linode Service Manager v0.1")
    log.info("loading instances state")
    service_model.run_init(global_config, fs_listener)
    # loading actual configurations
    log.info("loading configuration files")
    if fs_listener.isdir(global_config.config_dir):
        for fname in fs_listener.listdir(global_config.config_dir):
            if fname.startswith("."): continue
            log.info("... loading file: %s" % fname)
            data = fs_listener.readfile(global_config.config_dir + '/' + fname)
            try: service_model.update_config(fname, json.loads(data))
            except: traceback.print_exc()
    # init is done
    log.info("initialization done")

def run_main():
    # stateless init
    run_init()
    # checking if run is a dry-run to check if all libraries are imported correctly
    if sys.argv[1:] == ['test']:
        return
    
    # not a test: actual run
    """ Main function, runs forever. """
    log.info("observing filesystem changes")
    fs_listener.join()

if __name__ == "__main__":
    run_main()
