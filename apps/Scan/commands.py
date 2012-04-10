#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command
from uliweb.orm import get_model,do_,Begin,Commit
from uliweb import settings
from sqlalchemy.sql import and_,select


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
        from copyright import get_file_crbits2,crbits2crtype
        
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
                isbin = False
                if c[:4]=='\x7fELF':
                    isbin = True
                elif c[:8]=='!<arch>\n':
                    isbin = True
                if not isbin:
                    for m in cobj_copyright.finditer(c):
                        d = m.groupdict()
                        if d['copyright']:
                            copyright = True
                        if d['inhouse']:
                            copyright_inhouse = True
                        if d['gpl']:
                            copyright_gpl = True
                        if d['oos']:
                            copyright_oos = True
                crbits = get_file_crbits2(copyright,copyright_inhouse,copyright_gpl,copyright_oos)
                crtype = crbits2crtype(crbits)
                do_(ScanPathes.table.update()
                    .where(ScanPathes.c.id==path.id)
                    .values(copyright=copyright,
                            copyright_inhouse=copyright_inhouse,
                            copyright_gpl=copyright_gpl,
                            copyright_oos=copyright_oos,
                            crbits = crbits,
                            crtype = crtype,)
                    )
            count+=1
            s = "%d"%(count)
            out = "%s%s"%(nback*"\b",s)
            print out,
            nback = len(s)+1
        Commit()

class ScanDecideAllDirecotryCommand(Command):
    name = 'scdad'
    help = 'Scan decide all directory'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        ScanPathes = get_model("scanpathes")
        root_dp = settings.SCAN.DIR
        from copyright import crbits2crtype,get_file_crbits
        
        def get_path(id):
            r = select(ScanPathes.c, ScanPathes.c.id==id).execute()
            return r.fetchone()
        
        def get_children_pathes(id):
            r = select(ScanPathes.c, ScanPathes.c.parent==id).execute()
            return r.fetchall()
        
        def decide_directory(id):
            path = get_path(id)
            if path.type == 'f':
                crbits=get_file_crbits(path)
                crtype = crbits2crtype(crbits)
            else:
                #print "dir %d crtype ?"%(id)
                crbits = 0x00
                for p in get_children_pathes(id):
                    result = decide_directory(p.id)
                    if result>0:
                        crbits |= result
                crtype = crbits2crtype(crbits)
            if (path.crtype!=crtype) or (path.crbits!=crbits):
                do_(ScanPathes.table.update().where(ScanPathes.c.id==path.id).values(crtype=crtype,crbits=crbits))
                if path.type == 'd':
                    print "dir %d crtype = %d,%s"%(id,crtype,path.path)
            return crbits
        
        Begin()
        decide_directory(1)
        Commit()

class ScanExportConflictCommand(Command):
    name = 'scec'
    help = 'Scan export conflict'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        ScanPathes = get_model("scanpathes")
        root_dp = settings.SCAN.DIR
        
        from copyright import CRTYPE_COPYRIGHT_CONFLICT
        import re
        
        cobj = re.compile(settings.SCAN.RE_COPYRIGHT,re.M|re.I)
        
        count = 1
        for path in ScanPathes.filter(ScanPathes.c.crtype==CRTYPE_COPYRIGHT_CONFLICT).filter(ScanPathes.c.type=='f'):
            print count,path.path
            count+=1


class ScanTestCommand(Command):
    name = 'sctest'
    help = 'Scan test'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        import os,re
        
        def test1():
            print settings.SCAN.RE_COPYRIGHT
            cobj_copyright = re.compile(settings.SCAN.RE_COPYRIGHT,re.MULTILINE)
            root_dp = settings.SCAN.DIR
            fp = os.path.join(root_dp,"Makefile")
            f = open(fp)
            c = f.read()
            f.close()
            m = cobj_copyright.search(c)
            print m,m.group('inhouse'),m.group('gpl'),m.group('oos')
        
        def test2():
            ScanPathes = get_model("scanpathes")
            r = select(ScanPathes.c, ScanPathes.c.id==1).execute()
            row = r.fetchone()
            print row['path']
        
        def test3():
            ScanPathes = get_model("scanpathes")
            id = 1
            path = ScanPathes.get(id)
            print path.path,path.crbits,path.crtype
            crbits = 0x00
            for path in ScanPathes.filter(ScanPathes.c.parent==id):
                print path.path,path.crbits,path.crtype
                crbits |= path.crbits
            print crbits
        def test4():
            print "-"*60
            from copyright import CRTYPE_COPYRIGHT_CONFLICT,get_copyright_lines
            ScanPathes = get_model("scanpathes")
            root_dp = settings.SCAN.DIR
            pathes = ScanPathes.filter(ScanPathes.c.crtype==CRTYPE_COPYRIGHT_CONFLICT).filter(ScanPathes.c.type=='f')
            cobj = re.compile(settings.SCAN.RE_COPYRIGHT,re.M|re.I)
            for path in pathes:
                fp = os.path.join(root_dp,path.path)
                l = get_copyright_lines(fp,cobj)
                
                break
        test4()
