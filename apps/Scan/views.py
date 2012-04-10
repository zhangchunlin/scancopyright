#coding=utf-8
from uliweb import expose
from uliweb.orm import get_model
from os.path import split
#from sqlalchemy.sql import and_
from utils import get_path_css


@expose('/')
def index():
    return {}

def get_treenode(children,data=[]):
    from copyright import CRTYPE2CSSTAG 
    for path in children:
        if path.type=='d':
            isparent = 'true'
        else:
            isparent = 'false'
        name = split(path.path)[-1]
        d = {'id':'%d'%(path.id),'pId':'%d'%(path.parent.id),'name':name,'isParent':isparent}
        if path.type=='f':
            d['url']="/file/%d"%(path.id)
        if path.crtype>=0:
            d['css']=CRTYPE2CSSTAG[path.crtype]
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
    return data

@expose('/treenode')
def treenode():
    ScanPathes = get_model("scanpathes")
    
    if not request.POST.has_key('id'):
        p = ScanPathes.get(1)
        data = [{'id':'1','pId':'0','name':settings.SCAN.DIR,'open':'true','isParent':'true'},]
        
        children = ScanPathes.filter(ScanPathes.c.parent==1)
    else:
        data = []
        id = request.POST['id']
        children = ScanPathes.filter(ScanPathes.c.parent==id)
    
    data = get_treenode(children,data)
        
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
    from utils import text2html,tagcopyright
    ScanPathes = get_model("scanpathes")
    path = ScanPathes.get(id)
    assert(path.type=='f')
    fp = os.path.join(settings.SCAN.DIR,path.path)
    f = open(fp)
    content = text2html(tagcopyright(f.read()))
    f.close()
    return {
        'fp':text2html(fp),
        'content':content,
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
    
    from copyright import CRTYPE_COPYRIGHT_CONFLICT,get_copyright_lines
    from utils import text2html,tagcopyright
    
    pathes = ScanPathes.filter(ScanPathes.c.crtype==CRTYPE_COPYRIGHT_CONFLICT).filter(ScanPathes.c.type=='f')
    return {
        'pathes':pathes,
        'get_copyright_lines':get_copyright_lines,
        'text2html':text2html,
        'tagcopyright':tagcopyright,
    }
