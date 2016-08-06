#!/usr/bin/python3
# -*- coding: utf-8 -*-

import unittest
#
import os, tempfile, time

from dictlist_utils import dict_obj
from watchdog.observers import Observer
from fslistener_local import ConfigurationChangeHandler

class LocalFSListenerTest(unittest.TestCase):
    
    callback = None
    fslistener = None
    tmpdir = None
    actions = None
    
    def setUp(self):
        # creating empty callback
        cb = self.callback = dict_obj()
        sa = self.actions = list()
        cb.rename_config = lambda oldname, newname: sa.append(('r', oldname, newname))
        cb.update_config = lambda cname, json: sa.append(('u', cname, json))
        cb.save_config = lambda cname: sa.append(('s', cname,))
        cb.delete_config = lambda cname: sa.append(('d', cname,))
        # creating tmpdir
        td = self.tmpdir = tempfile.mkdtemp("", "pyunittest_fslistener_")
        # creating fslistener
        fl = self.fslistener = ConfigurationChangeHandler(cb, td)
        observer = Observer()
        observer.schedule(fl, path=self.tmpdir, recursive=True)
        observer.start()
    
    def test_move(self):
        print ("Testing onMove()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        with open(fulln, "w") as fp:
            fp.truncate(0)
            fp.write("{}")
        # preparing
        sa = self.actions
        time.sleep(1)
        sa.clear()
        # acting
        os.rename(fulln, fulln + ".rename")
        # checking
        time.sleep(1)
        assert os.path.isfile(fulln + ".rename")
        self.assertIn(('r', fn, fn + ".rename"), sa, "expected action list has rename")
        # uninit
        os.unlink(fulln + ".rename")
    
    def test_create(self):
        print ("Testing onCreate()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        assert not os.path.exists(fulln)
        # preparing
        sa = self.actions
        time.sleep(1)
        sa.clear()
        # acting
        with open(fulln, "w") as fp:
            fp.write("{}")
        # checking
        time.sleep(1)
        assert os.path.isfile(fulln)
        self.assertIn(('u', fn, {}), sa, "expected new file action")
        # uninit
        os.unlink(fulln)
    
    def test_delete(self):
        print ("Testing onDelete()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        assert not os.path.exists(fulln)
        # preparing
        with open(fulln, "w") as fp:
            fp.write("{}")
        sa = self.actions
        time.sleep(1)
        sa.clear()
        # acting
        os.unlink(fulln)
        # checking
        time.sleep(1)
        assert not os.path.exists(fulln)
        self.assertIn(('d', fn), sa, "expected new file action")
        # uninit
        pass
    
    def test_modify(self):
        print ("Testing onModify()")
        fn = "test_1.file"
        fulln = self.tmpdir + "/" + fn;
        assert not os.path.exists(fulln)
        # preparing
        with open(fulln, "w") as fp:
            fp.write("{}")
        sa = self.actions
        time.sleep(1)
        sa.clear()
        # acting
        with open(fulln, "w") as fp:
            fp.truncate(0)
            fp.write('{"abraka":"dabra"}')
        # checking
        time.sleep(1)
        self.assertIn(('u', fn, {"abraka":"dabra"}), sa, "expected new file action")
        # uninit
        os.unlink(fulln)
    
    def tearDown(self):
        # removing fslistener
        self.fslistener = None
        # removing tmpdir
        os.rmdir(self.tmpdir)
