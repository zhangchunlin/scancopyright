#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import *


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
    
    release = Field(bool,default= False)
    rnote = Field(str,max_length=512)

class Exts(Model):
    ext = Field(str,max_length=20,default="")
    num = Field(int)

class CopyrightInfo(Model):
    path = Reference(ScanPathes)
    crindex = Field(int)
    ibegin = Field(int)
    iend = Field(int)
