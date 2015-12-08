#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import *
from os.path import split
from copyright import crtype2csstag

class ScanPathes(Model):
    path = Field(str,max_length=2048)
    #d is dir,f is file,does not scan link
    type = Field(str,max_length=2)
    parent = SelfReference()
    ext = Field(str,max_length=20,default="")
    #copyright.CRTYPE_*
    crtype = Field(int,default= -1)
    #copyright.CRBITS_*
    crbits = Field(int,default= 0)
    copyright = Field(bool,default= False)
    copyright_inhouse = Field(bool,default= False)
    copyright_gpl = Field(bool,default= False)
    copyright_oos = Field(bool,default= False)

    #crindex_list = Field(str,max_length=400,default="")
    crindex_bits = Field(int,default=0)
    cribegin = Field(int,default=-1)
    criend = Field(int,default=-1)

    package_root  = Field(bool,default = False)
    release = Field(bool,default = False)
    rnote = Field(str,max_length=512)

    def to_api_dict(self):
        isparent = (self.type == 'd')
        return {'id':'%d'%(self.id),'pid':self.parent,'name':split(self.path)[-1],'isparent':isparent,'csstag':crtype2csstag(self.crtype),'release':self.release,'package_root':self.package_root,'rnote':self.rnote,'selected':False}

class Exts(Model):
    ext = Field(str,max_length=20,default="")
    num = Field(int)

class CopyrightInfo(Model):
    path = Reference("scanpathes")
    crindex = Field(int)
    ibegin = Field(int)
    iend = Field(int)
