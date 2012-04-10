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
    crbits = Field(int,default= -1)
    copyright = Field(bool,default= False)
    copyright_inhouse = Field(bool,default= False)
    copyright_gpl = Field(bool,default= False)
    copyright_oos = Field(bool,default= False)

class Exts(Model):
    ext = Field(str,max_length=20,default="")
    num = Field(int)
