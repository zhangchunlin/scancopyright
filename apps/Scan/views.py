#coding=utf-8
from uliweb import expose
from uliweb.orm import get_model
from os.path import split

@expose('/')
def index():
    return {}

def get_treenode(children,data=[]):
    for path in children:
        if path.type=='d':
            isparent = 'true'
        else:
            isparent = 'false'
        name = split(path.path)[-1]
        data.append({'id':'%d'%(path.id),'pId':'%d'%(path.parent.id),'name':name,'isParent':isparent})
    return data

@expose('/treenode')
def treenode():
    ScanPathes = get_model("scanpathes")
    
    if not request.POST.has_key('id'):
        p = ScanPathes.get(1)
        data = [{'id':'1','pId':'0','name':settings.SCAN.DIR,'open':'true'},]
        
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
    order = request.GET.get('order','index')
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
