#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#===============================================================================
#     File: $Name: utils.py $
# Revision: $Rev: 9f3a7b71 $
#  Created: $Date: 2014-06-29 00:52:50 $
# Modified: $Date: 2014-06-29 00:53:50 $
#   Author: $Author: Linh Vu Hong<lvho@dtu.dk> $
#-------------------------------------------------------------------------------
# Description: 
#===============================================================================
import sys
class Logger(object):
    def __init__(self,f):
        self.f = f
    def critical(self,msg,*args,**kwargs):
        self.f.write((msg % args) + "\n")

    def warning(self,msg,*args,**kwargs):
        self.f.write("WARNING: "+ (msg % args) + "\n")

    def error(self,msg,*args,**kwargs):
        self.f.write("ERROR: " + (msg % args) + "\n")

    info = critical
    debug = critical

class NullLogger(object):
    def __getattribute__(self,name):
        return self
    def __call__(self,*args,**kwargs):
        return self
