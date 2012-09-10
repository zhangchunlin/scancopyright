#coding=utf-8
from uliweb import expose
from uliweb.orm import get_model
from os.path import split
#from sqlalchemy.sql import and_
from utils import get_path_css


@expose('/')
def index():
    from copyright import crtype2csstag
    def get_dir_html(path):
        tag = crtype2csstag(path.crtype)
        html = '<%s>path</%s>: <a href="/dir/%d">%s</a>'%(tag,tag,path.id,path.path)
        return html
    def get_cr_html(path):
        ibits = path.crindex_bits
        if ibits==0:
            return ""
        else:
            html = "<ul>"
            index = 0
            while ibits!=0:
                if ibits&0x01!=0 and index!=0:
                    html+="<li>%s</li>"%(settings.SCAN.RE_LIST[index][1])
                ibits=(ibits>>1)
                index+=1
            html += "</ul>"
        return html
    ScanPathes = get_model("scanpathes")
    pathes = ScanPathes.filter(ScanPathes.c.release==True).order_by(ScanPathes.c.id.desc())
    return {
        'pathes':pathes,
        'get_dir_html':get_dir_html,
        'get_cr_html':get_cr_html,
    }

def get_treenode(children,data=[],under_release=False):
    from copyright import crtype2csstag
    for path in children:
        if path.type=='d':
            isparent = 'true'
        else:
            isparent = 'false'
        name = split(path.path)[-1]
        d = {'id':'%d'%(path.id),'pId':'%d'%(path.parent.id),'name':name,'isParent':isparent}
        if path.type=='f':
            d['url']="/file/%d"%(path.id)
        else:
            d['url']="/dir/%d"%(path.id)
        if path.crtype>=0:
            d['css']=crtype2csstag(path.crtype)
        if path.release:
            d['release']=u"★"
        data.append(d)
    def cmppath(x,y):
        if x['isParent']!=y['isParent']:
            return cmp(y['isParent'],x['isParent'])
        else:
            return cmp(x['name'].lower(),y['name'].lower())
    data.sort(cmppath)
    for d in data:
        if d.has_key('css'):
            d['name']= "<%s>%s</%s>"%(d['css'],d['name'],d['css'])
            del d['css']
        if d.has_key('release'):
            d['name']+=d['release']
            del d['release']
        elif under_release:
            d['name']+= u'✓'
    return data

@expose('/treenode')
def treenode():
    ScanPathes = get_model("scanpathes")
    def under_release(cid):
        while 1:
            path = ScanPathes.get(int(cid))
            #print cid,repr(path)
            if path.release or (path.parent==None):
                break
            else:
                cid = path.parent.id
        return path.release
    
    if not request.POST.has_key('id'):
        id = 1
        p = ScanPathes.get(id)
        data = [{'id':'1','pId':'0','name':settings.SCAN.DIR,'open':'true','isParent':'true'},]
    else:
        id = request.POST['id']
        data = []
    children = ScanPathes.filter(ScanPathes.c.parent==id)
    
    ur = under_release(id)
    
    data = get_treenode(children,data,ur)
    
    return json(data)

@expose('/exts')
def exts():
    offset = int(request.GET.get('from',0))
    order = request.GET.get('order','id')
    desc = int(request.GET.get('desc',0))
    Exts = get_model("exts")
    exts = Exts.all()
    if order == "num":
        if desc:
            exts=exts.order_by(Exts.c.num.desc())
        else:
            exts=exts.order_by(Exts.c.num.asc())
    else:
        if desc:
            exts=exts.order_by(Exts.c.id.desc())
    exts = exts.offset(offset).limit(settings.SCAN.RECORD_PER_PAGE)
    next_offset = offset+settings.SCAN.RECORD_PER_PAGE
    have_next = (Exts.all().count()>next_offset)
    last_offset = offset-settings.SCAN.RECORD_PER_PAGE
    have_last = (last_offset>=0)
    return {
        'offset':offset,
        'exts':exts,
        'next_offset':next_offset,
        'have_next':have_next,
        'last_offset':last_offset,
        'have_last':have_last,
        'order':order,
        'desc':desc,
    }

@expose('/ext/<int:id>')
def ext(id):
    Exts = get_model("exts")
    ext = Exts.get(id)
    ext_str = ext.ext
    ScanPathes = get_model("scanpathes")
    pathes = ScanPathes.filter(ScanPathes.c.type=='f').filter(ScanPathes.c.ext==ext_str)
    return {
        'pathes':pathes,
        'get_path_css':get_path_css,
    }

@expose('/file/<int:id>')
def file(id):
    import os
    from copyright import text2html,tagcopyright
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)
    assert(path.type=='f')
    fp = os.path.join(settings.SCAN.DIR,path.path)
    f = open(fp)
    content = text2html(tagcopyright(f.read()))
    f.close()
    return {
        'path':path,
        'fp':fp,
        'content':content,
    }

@expose('/dir/<int:id>')
def dir(id):
    def tagstring(str,tag):
        return "<%s>%s</%s>"%(tag,str,tag)
    PTYPE2URI = {
        'f':'file',
        'd':'dir'
    }
    from copyright import crtype2csstag
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)
    assert(path.type=='d')
    children = ScanPathes.filter(ScanPathes.c.parent==path.id)
    
    from forms import ReleaseForm
    rform = ReleaseForm()
    if request.method == 'POST':
        if rform.validate(request.params, request.files):
            release = rform.data['release']
            rnote = rform.data['rnote']
            changed = False
            if release!=path.release:
                path.release=release
                changed = True
                if release:
                    flash("Release this package !")
                else:
                    flash("Do not release this package !")
            if rnote!=path.rnote:
                path.rnote = rnote
                changed = True
            if changed:
                path.save()
    else:
        rform.data['release']=path.release
        rform.data['rnote']=path.rnote
    return {
        'path':path,
        'children':children,
        'crtype2csstag':crtype2csstag,
        'tagstring':tagstring,
        'PTYPE2URI':PTYPE2URI,
        'rform':rform,
    }

@expose('/copyright')
def copyright():
    from forms import CopyrightSearchForm,CrconflictForm
    cform = CrconflictForm(action='crconflict',method='get')
    sform = CopyrightSearchForm()
    if request.method == 'POST':
        if sform.validate(request.params, request.files):
            c = sform.data['c']
            ci = sform.data['ci']
            cg = sform.data['cg']
            co = sform.data['co']
            ScanPathes = get_model("scanpathes")
            pathes = ScanPathes.filter(ScanPathes.c.type=='f')
            if c!='0':
                #print "add filter copyright=%s"%(c=='1')
                pathes = pathes.filter(ScanPathes.c.copyright == (c=='1'))
            if ci!='0':
                #print "add filter copyright_inhouse=%s"%(ci=='1')
                pathes = pathes.filter(ScanPathes.c.copyright_inhouse == (ci=='1'))
            if cg!='0':
                #print "add filter copyright_gpl=%s"%(cg=='1')
                pathes = pathes.filter(ScanPathes.c.copyright_gpl == (cg=='1'))
            if co!='0':
                #print "add filter copyright_oos=%s"%(co=='1')
                pathes = pathes.filter(ScanPathes.c.copyright_oos == (co=='1'))
    else:
        pathes=None
    return {
        'cform':cform,
        'sform':sform,
        'pathes':pathes,
        'get_path_css':get_path_css,
    }

@expose('/crconflict')
def crconflict():
    ScanPathes = get_model("scanpathes")
    
    from copyright import CRTYPE_COPYRIGHT_CONFLICT,text2html,tagcopyright
    
    pathes = ScanPathes.filter(ScanPathes.c.crtype==CRTYPE_COPYRIGHT_CONFLICT).filter(ScanPathes.c.type=='f')
    return {
        'pathes':pathes,
        'text2html':text2html,
        'tagcopyright':tagcopyright,
    }

@expose('/ltypes')
def ltypes():
    return {
        "get_model":get_model,
    }

@expose('/allcrfiles/<int:pindex>.html')
def allcrfiles(pindex):
    ScanPathes = get_model("scanpathes")
    num = settings.SCAN.CRFILES_PER_PAGE
    offset = pindex*num
    pathes = ScanPathes.filter(ScanPathes.c.type=='f').filter(ScanPathes.c.crbits!=0)
    pagenum = (pathes.count()+(num-1))/num
    pathes = pathes.offset(offset).limit(num)
    return {
        'pathes':pathes,
        'pagenum':pagenum,
        'pindex':pindex
}

from Scan.copyright import *
@expose('/allcrfiles/crsnippet/<int:pathid>.html')
def crsnippet(pathid):
    import os
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(pathid)
    fp = os.path.join(settings.SCAN.DIR,path.path)
    snappet_txt = get_snappet(fp,path.cribegin,path.criend)
    snappet = text2html(tagcopyright(snappet_txt))
    return {
    "fpath":path.path,
    "snappet":snappet,
}
