#coding=utf-8
from uliweb import expose
from uliweb.orm import get_model
from os.path import split
#from sqlalchemy.sql import and_
from utils import get_path_css
import os

@expose('/')
def index():
    return {}

def get_subtree(id,open=False):
    if id<0:
        return 0,[]

    ScanPathes = get_model("scanpathes")
    if id==0:
        cnum = 1
        d = ScanPathes.get(1).to_api_dict()
        d['name'] = settings.SCAN.DIR
        d['open'] = open
        n,l = get_subtree(1,open)
        d['cnum'] = n
        d['subtree'] = l
        d['release'] = False
        clist = [d]
    else:
        children = ScanPathes.filter(ScanPathes.c.parent==id)
        cnum = children.count()
        clist = []
        if open:
            for path in children:
                d = path.to_api_dict()
                d['open'] = False
                if d['isparent']:
                    n,l = get_subtree(int(d['id']),False)
                    d['cnum'] = n
                    d['subtree'] = l
                else:
                    d['cnum'] = 0
                    d['subtree'] = []
                d['release'] = d['release']
                clist.append(d)
    return cnum,clist

@expose('/api/subtree/<int:id>')
def api_subtree(id):
    open = (request.GET.get('open','false')=='true')
    cnum,clist = get_subtree(id,open)

    return json(clist)

@expose('/api/pathinfo/<int:id>')
def api_pathinfo(id):
    ScanPathes = get_model("scanpathes")
    p = ScanPathes.get(id)
    d = p.to_dict()
    d['csstag'] = crtype2csstag(d['crtype'])
    return json(d)

@expose('/api/rlist')
def api_rlist():
    ScanPathes = get_model("scanpathes")
    pathes = ScanPathes.filter(ScanPathes.c.release==True).order_by(ScanPathes.c.id.desc())
    l = []
    for p in pathes:
        d = p.to_dict()
        d['csstag'] = crtype2csstag(d['crtype'])
        l.append(d)
    return json(l)

@expose('/api/setrelease/<int:id>')
def api_setrelease(id):
    r = request.POST.get('value',None)
    act = False
    if r!=None:
        ScanPathes = get_model("scanpathes")
        p = ScanPathes.get(id)
        r = (r=="true")
        act = (p.release!=r)
        if act:
            p.release = bool(r)
            p.save()
        return json({"ret":"ok","act":act})
    return json({"ret":"fail","act":act})

@expose('/api/setrnote/<int:id>')
def api_setrnote(id):
    rnote = request.POST.get('value',None)
    act = False
    if rnote!=None:
        ScanPathes = get_model("scanpathes")
        p = ScanPathes.get(id)
        act = (p.rnote!=rnote)
        if act:
            p.rnote = rnote
            p.save()
        return json({"ret":"ok","act":act})
    return json({"ret":"fail","act":act})

@expose('/inc/ftxt/<int:id>')
def inc_ftxt(id):
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)
    if path and path.type=='f':
        fp = os.path.join(settings.SCAN.DIR,path.path)
        f = open(fp)
        content = text2html(tagcopyright(f.read(1024)))
        b = f.read(1)
        if b!="":
            content += '<br/><a href="/file/%d">...<br/>click to show whole file</a>'%(id)
    else:
        content = ""
    return content

@expose('/inc/pathcr/<int:id>')
def inc_pathcr(id):
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)

    ibits = path.crindex_bits
    if ibits==0:
        return ""
    else:
        html = "<ul>"
        index = 0
        while ibits!=0:
            if ibits&0x01!=0 and index!=0:
                csstag = "cr_%s"%(settings.SCAN.RE_LIST[index][0])
                html+='<li><span class="%s">%s</span></li>'%(csstag,settings.SCAN.RE_LIST[index][1])
            ibits=(ibits>>1)
            index+=1
        html += "</ul>"
    return html

@expose('/inc/pathrnote/<int:id>')
def inc_pathrnote(id):
    from copyright import text2html

    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)

    html = text2html(path.rnote)
    return html

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

@expose('/view/<int:id>')
def view(id):
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)
    if path.type=='f':
        return redirect("/file/%d"%(id))
    else:
        return redirect("/dir/%d"%(id))

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

@expose('/allcrfiles/crsnippet/<int:pathid>.html')
def crsnippet(pathid):
    import os
    from Scan.copyright import tagcopyright,text2html,get_snappet
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(pathid)
    fp = os.path.join(settings.SCAN.DIR,path.path)
    snappet_txt = get_snappet(fp,path.cribegin,path.criend)
    snappet = text2html(tagcopyright(snappet_txt))
    return {
    "fpath":path.path,
    "snappet":snappet,
}
