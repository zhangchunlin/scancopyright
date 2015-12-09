#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command


class ScanAllCommand(Command):
    name = 'scall'
    help = 'Do all scan actions'

    def handle(self, options, global_options, *args):
        from utils import *
        self.get_application(global_options)
        scan_step_all_path()
        scan_step_all_copyright()
        scan_step_decide_all_dir()
        scan_step_import_package_list()
        scan_step_export_packages()

class ScanAllPathCommand(Command):
    name = 'scap'
    help = 'Scan all path'

    def handle(self, options, global_options, *args):
        from utils import scan_step_all_path
        self.get_application(global_options)
        scan_step_all_path()

class ScanAllCopyrightCommand(Command):
    name = 'scac'
    help = 'Scan all copyright'

    def handle(self, options, global_options, *args):
        from utils import scan_step_all_copyright
        self.get_application(global_options)
        scan_step_all_copyright()

class ScanDecideAllDirecotryCommand(Command):
    name = 'scdad'
    help = 'Scan decide all directory'

    def handle(self, options, global_options, *args):
        from utils import scan_step_decide_all_dir
        self.get_application(global_options)
        if len(args)>0:
            id = int(args[0])
        else:
            id = 1
        scan_step_decide_all_dir(id)

class ScanImportPackageListCommand(Command):
    name = 'scipl'
    help = 'Scan import package list'

    def handle(self, options, global_options, *args):
        from utils import scan_step_import_package_list
        self.get_application(global_options)
        scan_step_import_package_list()

class ScanExportOpenSourceCommand(Command):
    name = 'sceos'
    help = 'Scan Export Open Source'

    def handle(self, options, global_options, *args):
        from utils import scan_step_export_packages
        self.get_application(global_options)
        scan_step_export_packages()

class ScanExportScanInfoCommand(Command):
    name = 'scesi'
    help = 'Scan Export Scan Info'

    def handle(self, options, global_options, *args):
        from uliweb import settings

        self.get_application(global_options)

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
        from uliweb import settings
        from uliweb.utils.test import client

        import os

        self.get_application(global_options)

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
        from uliweb.utils.test import client
        from uliweb import settings

        import os

        self.get_application(global_options)

        if len(args)> 0:
            import re
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
        self.get_application(global_options)

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
        self.get_application(global_options)

        ScanPathes = get_model("scanpathes")
        f = open("release_package_list.txt","w")
        f.write("No.\tName\tLicense\n")
        index = 1
        for path in list(ScanPathes.filter(ScanPathes.c.release==True)):
            f.write("%d\t%s\t%s\n"%(index,path.path,path.rnote.replace("\r\n"," ")))
            index+=1
        f.close()
        print "export to release_package_list.txt"

class ScanCheckReleaseDirCommand(Command):
    name = 'sccrd'
    help = 'Scan Check Release Dir'

    def handle(self, options, global_options, *args):
        self.get_application(global_options)

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
-------------------------------
follow these steps to scan copyright:
- copy apps/local_setting.ini.example as apps/local_setting.ini
- modify local_settings.ini

[SCAN]
DIR = 'YOUR_SOURCE_CODE_PATH'
[ORM]
CONNECTION = 'sqlite:///DATABASE_NAME_YOU_WANT.db'

- uliweb syncdb (if you want to recreate database use: uliweb reset)
- uliweb scap (scan all path)
- uliweb scac (scan all copyright)
- uliweb scdad (decide all direcotry status)

-------------------------------
follow these steps to export
- modify local_settings.ini

[SCAN]
DIR_EXPORT = 'DIRECTORY_PATH_YOU_WANT_TO_EXPORT'

- use 'uliweb sceos' to export
'''

class ScanHelpCommand(Command):
    name = 'schelp'
    help = 'Scan Help'

    def handle(self, options, global_options, *args):
        self.get_application(global_options)
        print HELPMSG


class ScanTestCommand(Command):
    name = 'sctest'
    help = 'Scan test'

    def handle(self, options, global_options, *args):
        from uliweb import settings

        self.get_application(global_options)

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
