#!/usr/bin/python3
# -*- encoding: utf-8 -*-

from dictlist_utils import dict_obj
import os, logging, builtins
#
import json
import tunnel_ctl_service.modules

# this dictionary is filled up with other modules
provider_types = dict_obj() # provider_name (string) -> provider_class (type)

log = logging.getLogger("service_model")

def extract_cloud_provider(json_obj):
    try:
        cloud_provider = json_obj["server"]["cloud"]
    except AttributeError as e:
        raise e
    if cloud_provider not in provider_types:
        raise RuntimeError("cloud provider %s is not known" % cloud_provider)
    return provider_types[cloud_provider]

fsl = None # this object is initialized in run_init(...) method and provides access to filesystem (local or remote)
config_objs_dir = None
config_objs = dict_obj() # filename (string) -> config_file object

def run_init(config, ls):
    fsl = ls
    config_objs_dir = config.config_objs_dir
    # loading all modules handling changes from modules dir
    for im in tunnel_ctl_service.modules.__all__:
         if im == "__init__": continue
         builtins.__import__("tunnel_ctl_service.modules.%s" % im)
    # now loading state
    if fsl.isdir(config_objs_dir):
        for fname in fsl.listdir(config_objs_dir):
            if not fname.startswith("."): continue # all obj jsons
            data = fsl.readfile(config_objs_dir + '/' + fname)
            config = read_config_obj(json.loads(data))
            config_objs[fname] = config

def read_config_obj(json_obj):
    provider_type = extract_cloud_provider(json_obj)
    return provider_type(json_obj)

def update_config(fname, json_obj):
    """
    Updates existing config_obj or creates a new one.
    """
    obj_fname = generate_obj_file_name(fname)
    if obj_fname not in config_objs:
        # no config object: creating a new one
        provider_type = extract_cloud_provider(json_obj)
        config_obj = provider_type()
        config_obj.file_name = fname
        config_objs[obj_fname] = config_obj
    # 
    config_obj = config_objs[obj_fname]
    dict_update(config_obj, json_obj)

def dict_update(dobj, json_obj):
    for k,v in json_obj.items():
        ov = dobj.get(k)
        if (type(v) == dict or type(v) == dict_obj) and (type(ov) == dict or type(ov) == dict_obj):
            dict_update(ov, v)
        else:
            dobj[k] = v

def delete_config(fname):
    obj_fname = generate_obj_file_name(fname)
    if obj_fname not in config_objs:
        return # nothing to delete
    
    config_obj = config_objs[obj_fname]
    config_obj.server = {} # deinstallation
    try: fsl.unlink(config_objs_dir + "/" + obj_fname)
    except Exception: pass # already deleted? strange..
    del config_objs[obj_fname]

def save_config(fname):
    obj_fname = generate_obj_file_name(fname)
    log.info("saving configuration to file: " + obj_fname)
    if obj_fname not in config_objs:
        return # nothing to save
    config_obj = config_objs[obj_fname]
    with open(config_objs_dir + "/" + obj_fname, "w") as fp:
        fp.write(json.dumps(config_obj, indent = 2))

def rename_config(fname, newname):
    obj_fname = generate_obj_file_name(fname)
    if obj_fname not in config_objs:
        return # moved not existing file
    obj_newname = generate_obj_file_name(newname)
    config_objs[obj_newname].file_name = newname;
    config_objs[obj_newname] = config_objs[obj_fname]
    del config_objs[obj_fname]
    fsl.rename(config_objs_dir + "/" + obj_fname, config_objs_dir + "/" + obj_newname)

def generate_obj_file_name(fname):
    return "." + fname

"""
Model of server's configuration file.
It extends dict_obj, so its members can be accessed via 2 ways: .member and ["member"] .
Changing anything inside this config file is handled by modules.
"""
class config_file(dict_obj):
    
    def __init__(self, init_obj = { }):
        super().__init__(init_obj)
        self.server = None # those will be auto-converted to dict-objs because config_file itself is a dict_obj
        self.installation = None
        self.parameters = None
