#! /usr/bin/env python
#coding=utf-8

import re,cgi

CRBITS_NO = 0x00
CRBITS_COPYRIGHT = 0x01
CRBITS_COPYRIGHT_INHOUSE = 0x02
CRBITS_COPYRIGHT_GPL = 0x04
CRBITS_COPYRIGHT_OOS = 0x08

CRTYPE_NO_COPYRIGHT = 0x00
CRTYPE_COPYRIGHT = 0x01
CRTYPE_COPYRIGHT_INHOUSE = 0x02
CRTYPE_COPYRIGHT_GPL = 0x03
CRTYPE_COPYRIGHT_OOS = 0x04
CRTYPE_COPYRIGHT_MIXED = 0x05
CRTYPE_COPYRIGHT_CONFLICT = 0x06

CRTYPE2CSSTAG = ['cr_no','cr_cr','cr_ih','cr_gpl','cr_oos','cr_mixed','cr_conflict',]

def crbits2crtype(crbits):
    if crbits==CRBITS_NO:
        return CRTYPE_NO_COPYRIGHT
    elif crbits==CRTYPE_COPYRIGHT:
        return CRTYPE_COPYRIGHT
    elif (crbits&CRBITS_COPYRIGHT_INHOUSE)!=0 and (crbits&CRBITS_COPYRIGHT_GPL)!=0:
        return CRTYPE_COPYRIGHT_CONFLICT
    elif (crbits&CRBITS_COPYRIGHT_INHOUSE)!=0 and (crbits&CRBITS_COPYRIGHT_OOS)!=0:
        return CRTYPE_COPYRIGHT_MIXED
    elif (crbits&CRBITS_COPYRIGHT_INHOUSE)!=0:
        return CRTYPE_COPYRIGHT_INHOUSE
    elif (crbits&CRBITS_COPYRIGHT_GPL)!=0:
        return CRTYPE_COPYRIGHT_GPL
    elif (crbits&CRBITS_COPYRIGHT_OOS)!=0:
        return CRTYPE_COPYRIGHT_OOS
    else:
        return CRTYPE_COPYRIGHT

def get_file_crbits(path):
    crbits = 0x00
    if path.copyright:
        crbits |= CRBITS_COPYRIGHT
    if path.copyright_inhouse:
        crbits |= CRBITS_COPYRIGHT_INHOUSE
    if path.copyright_gpl:
        crbits |= CRBITS_COPYRIGHT_GPL
    if path.copyright_oos:
        crbits |= CRBITS_COPYRIGHT_OOS
    return crbits

def get_file_crbits2(copyright,copyright_inhouse,copyright_gpl,copyright_oos):
    crbits = 0x00
    if copyright:
        crbits |= CRBITS_COPYRIGHT
    if copyright_inhouse:
        crbits |= CRBITS_COPYRIGHT_INHOUSE
    if copyright_gpl:
        crbits |= CRBITS_COPYRIGHT_GPL
    if copyright_oos:
        crbits |= CRBITS_COPYRIGHT_OOS
    return crbits

def get_copyright_lines(fp,cobj):
    f = open(fp)
    txt = f.read()
    f.close()
    l = []
    txtlen = len(txt)
    ob = -1
    oe = -1
    for mobj in cobj.finditer(txt):
        b = mobj.start(0)
        e = mobj.end(0)
        #print "old",ob,oe,"new",b,e
        if (ob<0 or oe<0) or (not (ob<=b and oe>=e)):
            #print "before move:",b,e,txt[b:e]
            while b>0 and txt[b-1]!='\n':
                b-=1
            while e<txtlen and txt[e]!='\n':
                e+=1
            #print "after move:",b,e,txt[b:e]
            l.append(txt[b:e])
            ob = b
            oe = e
    return l

def get_snappet(fp,b,e):
    f = open(fp)
    txt = f.read()
    txtlen = len(txt)
    f.close()
    
    while b>0 and txt[b-1]!='\n': b-=1
    if b>0:
        while (1):
            nb = b-1
            while nb>0 and txt[nb-1]!='\n': nb-=1
            llen = b-nb
            strbegin = txt[nb:b][0:4]
            iscomment = (strbegin.find("*")!=-1) \
                or (strbegin.find("#")!=-1) \
                or (strbegin.find(";")!=-1)
            if llen>30 or iscomment:
                b = nb
                nb = b-1
                if nb<=0:
                    break
            else:
                break
            
    while e<txtlen and txt[e]!='\n': e+=1
    if e<txtlen:
        while (1):
            ne = e+1
            while ne<txtlen and txt[ne]!='\n': ne+=1
            llen = ne-e
            strbegin = txt[e+1:ne+4][0:4]
            iscomment = (strbegin.find("*")!=-1) \
                or (strbegin.find("#")!=-1) \
                or (strbegin.find(";")!=-1)
            
            if llen>30 or iscomment:
                e = ne
                ne = e+1
                if ne>=txtlen:
                    break
            else:
                break
    
    return txt[b:e]

def get_restring_from_relist(relist):
    index = 0
    l = []
    for tname,comment,restring in relist:
        l.append("(?P<i%d>%s)"%(index,restring))
        index += 1
    return "|".join(l)

def index2tname(index,relist):
    index = int(index[1:])
    return relist[index][0]

TNAME2CRBITS = {
    'cr':CRBITS_COPYRIGHT,
    'ih':CRBITS_COPYRIGHT_INHOUSE,
    'gpl':CRBITS_COPYRIGHT_GPL,
    'oos':CRBITS_COPYRIGHT_OOS,
}
def index2crbits(index,relist):
    index = int(index[1:])
    return TNAME2CRBITS[relist[index][0]]

def tagcopyright(text):
    from uliweb import settings
    from copyright import get_restring_from_relist
    
    re_list = settings.SCAN.RE_LIST
    def tagrepl(mobj):
        d = mobj.groupdict()
        tag = None
        for i,k in enumerate(d):
            if d[k]!=None:
                tag = "cr_%s"%(index2tname(k,re_list))
        if tag==None:
            return mobj.group(0)
        #print tag,mobj.group(0)
        return "{{{%s}}}%s{{{/%s}}}"%(tag,mobj.group(0),tag)
    restring = get_restring_from_relist(re_list)
    cobj = re.compile(restring,re.M|re.I)
    text = cobj.sub(tagrepl,text)
    return text

re_string_html = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)|(?P<protocal>(^|\s*)(http|ftp|https)://[\w\-\.,@?^=%&amp;:/~\+#]+)|(?P<tagcrbegin>\{\{\{)|(?P<tagcrend>\}\}\})', re.S|re.M|re.I)
re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)', re.S|re.M|re.I)
def text2html(text, tabstop=4, link=True):
    if not text:
        return ''
    def do_sub(m):
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br/>'
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;'*tabstop)
            t = t.replace(' ', '&nbsp;')
            return t
        elif c['tagcrbegin']:
            return '<'
        elif c['tagcrend']:
            return '>'
        else:
            url = m.group('protocal')
            if url.startswith(' '):
                prefix = ' '
                url = url[1:]
            else:
                prefix = ''
            return '%s<a href="%s">%s</a>' % (prefix, url, url)
    if link:
        return re.sub(re_string_html, do_sub, text)
    else:
        return re.sub(re_string, do_sub, text)