#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import get_model,do_,Begin,Commit
from sqlalchemy.sql import select#,and_
from copyright import *
import sys
import os

ERR_FILE_NOT_FOUND = 1
ERR_PACKAGE_COPYRIGHT_CONFLICT = 2
ERR_DIR_NOT_FOUND = 3

def get_path_css(path):
    cr = path.copyright
    cr_ih = path.copyright_inhouse
    cr_gpl = path.copyright_gpl
    cr_oos = path.copyright_oos
    if not(cr or cr_ih or cr_gpl or cr_oos):
        return 'no_cr'
    elif cr_ih and cr_gpl:
        return 'cr_conflict'
    elif cr_ih and cr_oos:
        return 'cr_mixed'
    elif cr_ih:
        return 'cr_ih'
    elif cr_gpl:
        return 'cr_gpl'
    elif cr_oos:
        return 'cr_oos'
    else:
        return 'cr'

def scan_step_all_path():
    from uliweb import settings

    ScanPathes = get_model("scanpathes")
    ScanPathes.remove()

    allext = {}
    root_dp = settings.SCAN.DIR
    ScanPathes(path = ".",type = "d",).save()

    count = 0
    Begin()

    IGNORE_DIRS_SET = set(settings.SCAN.DIR_IGNORE)
    for root,dirs,files in os.walk(root_dp):
        root_relp = os.path.relpath(root,root_dp)
        if not isinstance(root_relp,unicode):
            root_relp = root_relp.decode("utf8")
        print ".",
        rp = ScanPathes.get(ScanPathes.c.path==root_relp)
        if not rp:
            print "\ncan not find in db so do not scan %s"%(root)
            continue
        ignore_dirs = []
        for dn in dirs:
            dp = os.path.join(root,dn)
            if os.path.islink(dp):
                print "\nignore link:%s"%(dp)
                ignore_dirs.append(dn)
            elif dn in IGNORE_DIRS_SET:
                print "\nignore dir: %s"%(dp)
                ignore_dirs.append(dn)
            else:
                relp = os.path.relpath(dp,root_dp)
                do_(ScanPathes.table.insert().values(path = relp.decode("utf8"),type = "d",parent=rp.id))
        for dn in ignore_dirs:
            dirs.remove(dn)
        l = root.split(os.sep)
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
    print

def scan_step_all_copyright():
    import re
    from uliweb import settings

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
    tnum = ScanPathes.filter(ScanPathes.c.type=='f').count()
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
        s = "%d/%d"%(count,tnum)
        out = "%s%s"%(nback*"\b",s)
        print out,
        sys.stdout.flush()
        nback = len(s)+1
    Commit()

def scan_step_decide_all_dir(id=1):
    from uliweb import settings

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
            return path.crbits or 0,path.crindex_bits or 0
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

    print "want to decide %d"%(id)
    Begin()
    decide_path(id)
    Commit()
    path = get_path(id)
    print path.path,path.crindex_bits,path.crbits

def scan_step_export_packages():
    from uliweb import settings
    import shutil

    ScanPathes = get_model("scanpathes")

    dpexport = settings.SCAN.DIR_EXPORT

    if dpexport == None:
        print "err:pls set settings.SCAN.DIR_EXPORT"
        return

    paths = list(ScanPathes.filter(ScanPathes.c.release==True))
    if paths:
        if os.path.exists(dpexport):
            print "removing old %s ..."%(dpexport)
            shutil.rmtree(dpexport)
        print "create dir: %s"%(dpexport)
        os.mkdir(dpexport)

        print "begin to export"
        for path in paths:
            #print path.path
            dpdst = os.path.join(dpexport,path.path)
            if not os.path.exists(dpdst):
                os.makedirs(dpdst)
            dpsrc = os.path.join(settings.SCAN.DIR,path.path)
            cmd = "rsync -a --exclude .git %s/ %s/"%(dpsrc,dpdst)
            print "export: %s"%(path.path)
            #print "  cmd: %s"%(cmd)
            os.system(cmd)
        print "export finished, pls check '%s' directory for export result"%(dpexport)
    else:
        print >>sys.stderr, "error: no path to export"

def scan_step_import_package_list(fpath = None):
    from uliweb import settings
    if not fpath:
        project_list_fpath = os.path.join(settings.SCAN.DIR,".repo/project.list")
        if os.path.isfile(project_list_fpath):
            fpath = project_list_fpath

        if not os.path.isfile(project_list_fpath):
            print >>sys.stderr, "error: project list file not found"
            sys.exit(ERR_FILE_NOT_FOUND)

        ScanPathes = get_model("scanpathes")
        for line in open(fpath):
            line = line.strip()
            if line:
                scanpath = ScanPathes.get(ScanPathes.c.path==line)
                if scanpath:
                    touch = False
                    if not (scanpath.package_root==True):
                        print "update %s package_root = True"%(line)
                        scanpath.package_root = True
                        touch = True
                    crtype = crbits2crtype(scanpath.crbits)
                    if crtype==CRTYPE_COPYRIGHT_GPL:
                        if not (scanpath.release==True):
                            print "update %s release = True, because it is GPL"%(line)
                            scanpath.release = True
                            if not scanpath.rnote:
                                scanpath.rnote = "should release because GPL or LGPL"
                            touch = True
                    if crtype==CRTYPE_COPYRIGHT_CONFLICT:
                        print >>sys.stderr, "error: package '%s' copyright conflict"%(line)
                        sys.exit(ERR_PACKAGE_COPYRIGHT_CONFLICT)
                    if touch:
                        scanpath.save()
                else:
                    #print >>sys.stderr, "error: package '%s' not found"%(line)
                    #sys.exit(ERR_DIR_NOT_FOUND)
                    pass
