#! /usr/bin/env python
#coding=utf-8

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

CRTYPE2CSSTAG = ['no_cr','cr','cr_ih','cr_gpl','cr_oos','cr_mixed','cr_conflict',]

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
