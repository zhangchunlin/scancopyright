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

class ScanAllCopyrightCommand(Command):
    name = 'scac'
    help = 'Scan all copyright'
    
    def handle(self, options, global_options, *args):
        import os,re
        
        get_app()
        
        exts_ignore_dict = {}
        for ext in settings.SCAN.FILE_EXTS_IGNORE:
            exts_ignore_dict[ext]=True
        
        ScanPathes = get_model("scanpathes")
        files = ScanPathes.filter(ScanPathes.c.type=='f')
        cobj_copyright = re.compile(settings.SCAN.RE_COPYRIGHT,re.M)
        root_dp = settings.SCAN.DIR
        count = 0
        nback = 0
        Begin()
        for path in files:
            if not exts_ignore_dict.has_key(path.ext):
                fp = os.path.join(root_dp,path.path)
                f = open(fp)
                c = f.read()
                f.close()
                
                copyright=False
                copyright_inhouse=False
                copyright_gpl=False
                copyright_oos=False
                update = False
                
                for m in cobj_copyright.finditer(c):
                    d = m.groupdict()
                    if d['copyright']:
                        copyright = True
                        update = True
                    if d['inhouse']:
                        copyright_inhouse = True
                        update = True
                    if d['gpl']:
                        copyright_gpl = True
                        update = True
                    if d['oos']:
                        copyright_oos = True
                        update = True
                if update:
                    do_(ScanPathes.table.update().where(ScanPathes.c.id==path.id).values(copyright=copyright,copyright_inhouse=copyright_inhouse,copyright_gpl=copyright_gpl,copyright_oos=copyright_oos))
                else:
                    do_(ScanPathes.table.update().where(ScanPathes.c.id==path.id).values(copyright=False,copyright_inhouse=False,copyright_gpl=False,copyright_oos=False))
            count+=1
            s = "%d"%(count)
            out = "%s%s"%(nback*"\b",s)
            print out,
            nback = len(s)+1
        Commit()

class ScanTestCommand(Command):
    name = 'sctest'
    help = 'Scan test'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        import os,re
        
        print settings.SCAN.RE_COPYRIGHT
        cobj_copyright = re.compile(settings.SCAN.RE_COPYRIGHT,re.MULTILINE)
        root_dp = settings.SCAN.DIR
        fp = os.path.join(root_dp,"Makefile")
        f = open(fp)
        c = f.read()
        f.close()
        m = cobj_copyright.search(c)
        print m,m.group('inhouse'),m.group('gpl'),m.group('oos')
        