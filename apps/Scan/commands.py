#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command
from uliweb.orm import get_model,do_,Begin,Commit
from uliweb import settings


def get_app():
    from uliweb.manage import make_application
    app = make_application(start=False, debug_console=False, debug=False)
    return app

class ScanAllPathCommand(Command):
    name = 'scap'
    help = 'Scan all path'
    
    def handle(self, options, global_options, *args):
        import os
        
        get_app()
        
        ScanPathes = get_model("scanpathes")
        ScanPathes.remove()
        
        allext = {}
        root_dp = settings.SCAN.DIR
        ScanPathes(path = ".",type = "d",).save()
        
        count = 0
        Begin()
        for root,dirs,files in os.walk(root_dp):
            root_relp = os.path.relpath(root,root_dp)
            print ".",
            rp = ScanPathes.get(ScanPathes.c.path==root_relp)
            assert (rp!=None),"root=%s,root_relp:%s"%(root,root_relp)
            for dn in dirs:
                dp = os.path.join(root,dn)
                if not os.path.islink(dp):
                    relp = os.path.relpath(dp,root_dp)
                    do_(ScanPathes.table.insert().values(path = relp.decode("utf8"),type = "d",parent=rp.id))
                else:
                    print "\nignore link:%s"%(dp)
            l = root.split(os.sep)
            if "res" in l:
                print "\nignore res:%s"%(root)
                continue
            for fn in files:
                fp = os.path.join(root,fn)
                if not os.path.islink(fp):
                    p,ext = os.path.splitext(fn)
                    relp = os.path.relpath(fp,root_dp)
                    do_(ScanPathes.table.insert().values(path = relp.decode("utf8"),type = "f",ext=ext,parent=rp.id))
                    if allext.has_key(ext):
                        allext[ext] += 1
                    else:
                        allext[ext] = 1
                else:
                    print "\nignore link:%s"%(fp)
        Commit()
        
        Exts = get_model("exts")
        Exts.remove()
        for i,k in enumerate(allext):
            Exts(ext = k,num = allext[k]).save()
