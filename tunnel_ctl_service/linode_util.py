#!/usr/bin/python3

# core imports
import sys
import json
# utils
from dictlist_utils import dict_obj
import logging
# components
from tunnel_ctl_service import service_model
from linode.api import Api

log = logging.getLogger("linode")

# semplar.net key 'hvq1qgE2NPV2MCXFgita5uR2DRJ1TxLONbkryGUEAs4Ea6j5aMOMx0q8R3ToZuy1'
api_key = 'fQXt9hhePJhp759JdCPxVfEpg7o99IBDUNreCISGNd8GSFdzJfSnGWCwdmiCEF55'

def get_api():
    api = Api(api_key)
#     try:
#         # testing Linode's API echo returns correct result
#         assert api.test.echo(GIVEBACK = 1) == {'GIVEBACK' : 1}
#     finally:
#         pass # api is RESTful
    return api

def print_api_spec(api_spec):
    """
    Prints out api in handy text format.
    @param api_spec: JSON api spec returned from Linode API
    """
    api_spec = dict_obj(api_spec)
    print ("Linode API version: " + str(api_spec.VERSION))
    print ("note: `!` symbol after parameter names marks mandatory parameters")
    
    sorted_methods = sorted(api_spec.METHODS.items(), key=lambda x: x[0])
    for mname, minfo in sorted_methods:
        print ()
        param_names = []
        for _, pinfo in minfo.PARAMETERS.items():
            param_names.append(("!" if pinfo.REQUIRED else "") + pinfo.NAME + ":" + pinfo.TYPE)
        throws = minfo.THROWS
        if throws: throws = " throws " + throws
        print ("> " + mname + "(" + ", ".join(param_names) + ")" + throws)
        if minfo.DESCRIPTION: print (minfo.DESCRIPTION)
        for _, pinfo in minfo.PARAMETERS.items():
            if pinfo.DESCRIPTION:
                print ("    " + pinfo.NAME + (" (required)" if pinfo.REQUIRED else "") + ": " + pinfo.TYPE + " - " + pinfo.DESCRIPTION)

"""
Handlers tree, modules usually registers
"""
handlers = dict_obj()
def handlers_autoexpander(d, name):
    dd = d[name] = dict_obj()
    dd._set_def_value_func(handlers_autoexpander)
    return dd
handlers._set_def_value_func(handlers_autoexpander)

def register_path_change(path, handler):
    hnode = handlers
    ps = path.split(".")
    for pe in ps:
        hnode = hnode[pe]
    hnode._handler = handler

class linode_config_file(service_model.config_file):
    
    handle_updates = True
    
    def __init__(self, init_obj = { }):
        super().__init__(init_obj)
        self._add_change_handler(linode_config_file.handle_change)
    
    @staticmethod
    def handle_change(d, key, old_value, new_value):
        if not d.handle_updates: return
        # if nothing changed, we do nothing
        if old_value == new_value:
#            log.debug("configuration handler: value is not changed, doing nothing" % ".".join(key))
            return
        else:
            log.info("handling configuration change: %s" % ".".join(key))
        #
        hnode = handlers
        for i in key:
            hnode = hnode[i]
            # now handling path
            if "_handler" in hnode:
                hnode._handler(d, key, old_value, new_value)
        
        if not hnode: # excluding empty dict or None
            log.error("unsupported parameter ignored: %s" % key)
            return
        #
        if key[:1] == ("server",):
            #
            if key[1:2] == ("login",):
                # login/password is changed
                # TODO
                pass
            elif key[1:2] == ("distribution",):
                # distribution is changed
                # TODO
                pass
            elif key[1:2] == ("ram",):
                # ram is changed
                # TODO
                pass
            elif key[1:2] == ("cloud",):
                # cloud is changed
                # TODO
                pass
            else:
                pass
        elif key[:1] == ("installation",) and d.server:
            if key[1:] == ():
                full_install(d)
                #
        elif key[:1] == ("parameters",) and d.server:
            # TODO
            pass
        else:
            pass

def run_main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("requests").setLevel(logging.WARNING)
    args = sys.argv[1:]
    if not args:
        print ("no command specified, possible commands are:")
        print ("  print: prints various information; must be `print api`")
        print ("  call: evaluate call to api; example:test.echo()")
    else:
        api = get_api()
        if args == ['print', 'api']:
            print_api_spec(api.api.spec())
        elif args[0] == 'call':
            for i in args[1:]:
                print (json.dumps(eval("api." + i, globals(), locals()), check_circular=True, indent=2))
        elif args[0] == 'delete':
            for i in args[1:]:
                i = int(i)
                print ("deleting linode %i..." % i)
                delete_linode(i)
        else:
            print ("unsupported operation: " + args[0])

# registering Linode provider
service_model.provider_types.Linode = linode_config_file

from tunnel_ctl_service.modules.linode_basic import full_install, delete_linode

if __name__ == "__main__":
    run_main()
