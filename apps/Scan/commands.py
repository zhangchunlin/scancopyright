#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command
from uliweb.orm import get_model,do_,Begin,Commit
from uliweb import settings
from sqlalchemy.sql import select#,and_
from copyright import *


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
        CopyrightInfo = get_model('copyrightinfo')
        CopyrightInfo.remove()
        files = ScanPathes.filter(ScanPathes.c.type=='f')
        restring = get_restring_from_relist(settings.SCAN.RE_LIST)
        cobj_copyright = re.compile(restring,re.M)
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
                crbits = 0
                isbin = False
                
                crindex_bits = 0
                cribegin = -1
                criend = -1
                
                if c[:4]=='\x7fELF':
                    isbin = True
                elif c[:8]=='!<arch>\n':
                    isbin = True
                elif c[:6]=='CATI\x01\x00':
                    isbin = True
                if not isbin:
                    for m in cobj_copyright.finditer(c):
                        d = m.groupdict()
                        for i,k in enumerate(d):
                            if d[k]!=None:
                                index = int(k[1:])
                                crindex_bits |= (0x01<<index)
                                crbits |= index2crbits(k,settings.SCAN.RE_LIST)
                                ibegin = m.start(0)
                                iend = m.end(0)
                                do_(CopyrightInfo.table.insert()
                                    .values(path = path.id,
                                        crindex = index,
                                        ibegin = ibegin,
                                        iend = iend,
                                    )
                                )
                                if cribegin<0 or ibegin<cribegin:
                                    cribegin = ibegin
                                if criend<0 or iend>criend:
                                    criend = iend
                crtype = crbits2crtype(crbits)
                do_(ScanPathes.table.update()
                    .where(ScanPathes.c.id==path.id)
                    .values(copyright=((crbits&CRBITS_COPYRIGHT)!=0),
                            copyright_inhouse=((crbits&CRBITS_COPYRIGHT_INHOUSE)!=0),
                            copyright_gpl=((crbits&CRBITS_COPYRIGHT_GPL)!=0),
                            copyright_oos=((crbits&CRBITS_COPYRIGHT_OOS)!=0),
                            crbits = crbits,
                            crtype = crtype,
                            crindex_bits = crindex_bits,
                            cribegin = cribegin,
                            criend = criend
                            )
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
        
        def get_path(id):
            r = do_(select(ScanPathes.c, ScanPathes.c.id==id))
            return r.fetchone()
        
        def get_children_pathes(id):
            r = do_(select(ScanPathes.c, ScanPathes.c.parent==id))
            return r.fetchall()
        
        def decide_path(id):
            path = get_path(id)
            if path.type == 'f':
                return path.crbits,path.crindex_bits
            else:
                #print "dir %d crtype ?"%(id)
                crbits = 0x00
                crindex_bits = 0x00
                for p in get_children_pathes(id):
                    crbits_child,crindexbits_child = decide_path(p.id)
                    #print "\t",p.path
                    #print "\t%d|%d="%(crindex_bits,crindexbits_child),
                    crbits |= crbits_child
                    crindex_bits |= crindexbits_child
                    #print crindex_bits
                crtype = crbits2crtype(crbits)
                if (path.crtype!=crtype) or (path.crbits!=crbits) or (path.crindex_bits!=crindex_bits):
                    do_(ScanPathes.table.update().where(ScanPathes.c.id==path.id).values(crtype=crtype,crbits=crbits,crindex_bits=crindex_bits))
                print "%s\t0x%04x\t0x%08x\t%s"%(crtype2csstag(crtype)[3:8],crbits,crindex_bits,path.path)
            return crbits,crindex_bits
        
        if len(args)>0:
            id = int(args[0])
        else:
            id = 1
        print "want to decide %d"%(id)
        Begin()
        decide_path(id)
        Commit()
        path = get_path(id)
        print path.path,path.crindex_bits,path.crbits

class ScanExportScanInfoCommand(Command):
    name = 'scesi'
    help = 'Scan Export Scan Info'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        ScanPathes = get_model("scanpathes")
        CopyrightInfo = get_model("copyrightinfo")
        root_dp = settings.SCAN.DIR
        relist = settings.SCAN.RE_LIST
        
        def get_infos_by_id(id):
            r = do_(select(CopyrightInfo.c, CopyrightInfo.c.path==id))
            return r.fetchall()
        
        def get_path(id):
            r = do_(select(ScanPathes.c, ScanPathes.c.id==id))
            return r.fetchone()
        
        def get_children_pathes(id):
            r = do_(select(ScanPathes.c, ScanPathes.c.parent==id))
            return r.fetchall()
        
        def get_cr_info(id):
            infos = get_infos_by_id(id)
            crindexd = {}
            ibegin = -1
            iend = -1
            for info in infos:
                crindexd[info.crindex]=True
                if ibegin<0 or info.ibegin<ibegin:
                    ibegin = info.ibegin
                if iend<=0 or info.iend>iend:
                    iend = info.iend
            crinfostring = ""
            for i,k in enumerate(crindexd):
                crinfostring+="%s\x0a"%(relist[k][1])
            #print crindexd,crinfostring
            return crinfostring,(ibegin,iend)
        
        ICOL_DIR = 0
        ICOL_FILE = 1
        ICOL_CR = 2
        ICOL_IH = 3
        ICOL_GPL = 4
        ICOL_OOS = 5
        ICOL_SNIPPET = 6
        def ws_append(ws,p=None):
            irow = len(ws.rows)
            if p!=None:
                if p.type == 'f':
                    icol = ICOL_FILE
                else:
                    icol = ICOL_DIR
                ws.write(irow,icol,p.path)
                
                if p.type == 'f':
                    icol = 2
                    typestr,crstribe =get_cr_info(p.id)
                    #print "{",typestr,crstribe,"}"
                    ws.write(irow,icol,typestr)
                    #print irow,icol,typestr
            else:
                ws.write(irow,0,"")
        
        def traverse_directory(id,ws):
            dpath = get_path(id)
            print dpath.path
            children = get_children_pathes(id)
            files = []
            dirs = []
            for child in children:
                if child.type=='f':
                    files.append(child)
                elif child.type=='d':
                    dirs.append(child)
            if len(files)>0:
                ws_append(ws,dpath)
            
            for f in files:
                ws_append(ws,f)
            
            for d in dirs:
                traverse_directory(d.id,ws)
        
        w = Workbook()
        Begin()
        subd = ScanPathes.filter(ScanPathes.c.parent==6).filter(ScanPathes.c.type=='d')
        for p in subd:
            ws = w.add_sheet(p.path)
            traverse_directory(p.id,ws)
            ws.col(0).width=0x0d00+200
            ws.col(1).width=0x0d00+300
            ws.col(0).width=0x0d00+400
            
            fnt = Font()
            fnt.height = 200
            style = XFStyle()
            style.font = fnt
            ws.row(1).set_style(style)
            break
        Commit()
        w.save('scaninfos.xls')

class ScanExportAllCrSnippetCommand(Command):
    name = 'sceacs'
    help = 'Scan Export All Copyright Snippet'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        from uliweb.utils.test import client
        
        import os
        cwd = os.getcwd()
        
        c = client('.')
        
        ScanPathes = get_model("scanpathes")
        pathes = ScanPathes.filter(ScanPathes.c.type=='f').filter(ScanPathes.c.crbits!=0)
        num = settings.SCAN.CRFILES_PER_PAGE
        pagenum = (pathes.count()+(num-1))/num
        os.mkdir(os.path.join(cwd,'allcrfiles'))
        for i in range(pagenum):
            r = c.get('/allcrfiles/%d.html'%(i))
            fp = os.path.join(cwd,"allcrfiles/%d.html"%(i))
            f = open(fp,"w")
            f.write(r.data)
            f.close()
            print fp
        
        os.mkdir(os.path.join(cwd,'allcrfiles/crsnippet'))
        pathes = ScanPathes.filter(ScanPathes.c.type=='f').filter(ScanPathes.c.crbits!=0)
        for path in pathes:
            r = c.get('/allcrfiles/crsnippet/%d.html'%(path.id))
            fp = os.path.join(cwd,'allcrfiles/crsnippet/%d.html'%(path.id))
            f = open(fp,"w")
            f.write(r.data)
            f.close()
            print fp

class ScanShowFileCopyright(Command):
    name = 'scsfc'
    help = 'Scan Show File Copyright'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        if len(args)> 0:
            import os,re
            id = int(args[0])
            ScanPathes = get_model("scanpathes")
            path = ScanPathes.get(id)
            if path.type!='f':
                return
            root_dp = settings.SCAN.DIR
            restring = get_restring_from_relist(settings.SCAN.RE_LIST)
            cobj_copyright = re.compile(restring,re.M)
            fp = os.path.join(root_dp,path.path)
            print fp
            f = open(fp)
            c = f.read()
            f.close()
            crbits = 0
            l = []
            cribegin = -1
            criend = -1
            for m in cobj_copyright.finditer(c):
                d = m.groupdict()
                for i,k in enumerate(d):
                    if d[k]!=None:
                        indexstr = k[1:]
                        if indexstr not in l:
                            l.append(indexstr)
                        crbits |= index2crbits(k,settings.SCAN.RE_LIST)
                        ibegin = m.start(0)
                        iend = m.end(0)
                        if cribegin<0 or ibegin<cribegin:
                            cribegin = ibegin
                        if criend<0 or iend>criend:
                            criend = iend
            crtype = crbits2crtype(crbits)
            print crbits,crtype

class ScanImportPackageListTxtCommand(Command):
    name = 'sciplt'
    help = 'Scan Import Package List Txt'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        ScanPathes = get_model("scanpathes")
        
        fptxt = args[0]
        f = open(fptxt)
        for l in f:
            if len(l)>8:
                index,mpath,mstatus,mlicence_org = l.split('\t')
                mlicence = mlicence_org.strip().lower()
                if mlicence.find('gpl')!=-1:
                    if mlicence=='gpl' or mlicence=='lgpl':
                        path = ScanPathes.get(ScanPathes.c.path==mpath)
                        if path!=None:
                            path.release = True
                            path.rnote = "release as %s,status:%s"%(mlicence_org,mstatus)
                            path.save()
                            print "set %d %s as release"%(path.id,path.path)
                        else:
                            print mpath,"not found"
                    else:
                        print "warning,this mixed should handle manually:",index,mpath,mstatus,mlicence
        f.close()

class ScanExportReleasePackageListTxtCommand(Command):
    name = 'scexplt'
    help = 'Scan Export Release Package List Txt'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        ScanPathes = get_model("scanpathes")
        f = open("release_package_list.txt","w")
        f.write("No.\tName\tLicense\n")
        index = 1
        for path in list(ScanPathes.filter(ScanPathes.c.release==True)):
            f.write("%d\t%s\t%s\n"%(index,path.path,path.rnote.replace("\r\n"," ")))
            index+=1
        f.close()
        print "export to release_package_list.txt"

class ScanExportOpenSourceCommand(Command):
    name = 'sceos'
    help = 'Scan Export Open Source'
    
    def handle(self, options, global_options, *args):
        def create_dir(dp):
            root = "/"
            for n in dp.split(os.sep):
                root = os.path.join(root,n)
                
                if not os.path.exists(root):
                    #print "mkdir %s"%(root)
                    try:
                        os.mkdir(root)
                    except OSError,e:
                        print e
                        return False
            return True
        get_app()
        
        import os,shutil
        
        ScanPathes = get_model("scanpathes")
        
        dpexport = settings.SCAN.DIR_EXPORT
        
        if dpexport == None:
            print "err:pls set settings.SCAN.DIR_EXPORT"
            return
        
        if os.path.exists(dpexport):
            print "removing old %s ..."%(dpexport)
            shutil.rmtree(dpexport)
        os.mkdir(dpexport)
        
        for path in list(ScanPathes.filter(ScanPathes.c.release==True)):
            #print path.path
            dpdst = os.path.join(dpexport,path.path)
            create_dir(dpdst)
            dpsrc = os.path.join(settings.SCAN.DIR,path.path)
            assert(os.path.isdir(dpsrc))
            cmd = "rsync -av %s/ %s/"%(dpsrc,dpdst)
            print cmd
            os.system(cmd)

class ScanCheckReleaseDirCommand(Command):
    name = 'sccrd'
    help = 'Scan Check Release Dir'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        import os
        
        if len(args)>0:
            dprelease = args[0]
            if not os.path.exists(dprelease):
                print "err:%s not found"%(dprelease)
                return
            
            ScanPathes = get_model("scanpathes")
            
            print "list of pathes should release but not found:"
            for path in list(ScanPathes.filter(ScanPathes.c.release==True)):
                #print path.path
                dp = os.path.join(dprelease,path.path)
                if not os.path.exists(dp):
                    print "%s"%(path.path)

HELPMSG = '''
follow these step to scan copyright:
- modify local_setting.ini
    SCAN.DIR = 'YOUR SOURCE CODE PATH'
    ORM.CONNECTION = 'sqlite:///DATABASE_NAME_YOU_WANT.db'
- remove .git/.svn from your source code directory
- uliweb syncdb (if you want to recreate database use: uliweb reset)
- uliweb scap (scan all path)
- uliweb scac (scan all copyright)
- uliweb scdad (decide all direcotry status)
'''

class ScanHelpCommand(Command):
    name = 'schelp'
    help = 'Scan Help'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        print HELPMSG


class ScanTestCommand(Command):
    name = 'sctest'
    help = 'Scan test'
    
    def handle(self, options, global_options, *args):
        get_app()
        
        import os,re
        
        def test1():
            restring = get_restring_from_relist(settings.SCAN.RE_LIST)
            cobj_copyright = re.compile(restring,re.MULTILINE)
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
            ScanPathes = get_model("scanpathes")
            root_dp = settings.SCAN.DIR
            pathes = ScanPathes.filter(ScanPathes.c.crtype==CRTYPE_COPYRIGHT_CONFLICT).filter(ScanPathes.c.type=='f')
            restring = get_restring_from_relist(settings.SCAN.RE_LIST)
            cobj = re.compile(restring,re.M|re.I)
            for path in pathes:
                fp = os.path.join(root_dp,path.path)
                l = get_copyright_lines(fp,cobj)
                
                break
        def test5():
            ScanPathes = get_model("scanpathes")
            def get_path(id):
                r = do_(select(ScanPathes.c, ScanPathes.c.id==id))
                return r.fetchone()
            print get_path(1)
        test5()
