#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import *

class ScanPathes(Model):
    path = Field(str,max_length=2048)
    #d is dir,f is file,does not scan link
    type = Field(str,max_length=2)
    license = Field(str,max_length=10,default="")
    parent = SelfReference()
    ext = Field(str,max_length=20,default="")

class Exts(Model):
    ext = Field(str,max_length=20,default="")
    num = Field(int)
