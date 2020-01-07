# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 11:05:59 2020

@author: slee
"""

import logging

import tkinter as tk
import json

from os import path
#from datetime import date, datetime
#from Daq import *
#from mcc_daq import *
#from mcc_dio import *
#from Ext_trigger import *
#from Timer import Timer
import Stepper_control as stepper


logging.basicConfig(level=logging.INFO)
    
class Entryframe(tk.LabelFrame):
    def __init__(self, parent, data, framename=None):
        super().__init__(parent,text=framename)       
        self.hcomp = {}
        self.comp_dtype={}
        self.data =data
        self.framename = framename
        self.init_entrys()

    def init_entrys(self):            
            
        i=0
        for key,value in self.data.items():
            
            tk.Label(self, text=key).grid(row=i)
            
            h = tk.Entry(self)
            h.insert(0,value)
            h.grid(row=i, column=1)    
            self.hcomp[key]=h
            if type(value) == list:                
                self.comp_dtype[key]=[type(value),type(value[0])]
            else:
                self.comp_dtype[key]=[type(value)]
            i +=1  
        
        

 
    def update_par(self):
        """
        def update_par(self):
            update data structure from inputs
        """
        for key in self.data:                        
            h=self.hcomp[key]
            dtype = self.comp_dtype[key][0]
            value= h.get()
            if dtype ==list:
                dtype1 = self.comp_dtype[key][1]
                dtype_value = [dtype1(i) for i in value.split()]
                self.data[key]= dtype_value                
            else:
                self.data[key]=dtype(value)
            
            
    def entry_enable(self):
        for key in self.data:            
            h=self.hcomp[key]
            h.config(state='normal')
            
    def entry_disable(self):
        for key in self.data:            
            h=self.hcomp[key]
            h.config(state='disabled')



    
    
        

        
    
class Paramframe:
    def __init__(self, master,filename):        
        #here = path.abspath(path.dirname(__file__))
        #self.envfile = path.join(here,filename)
        self.envfile = path.join(filename)
        
        with open(self.envfile) as envf:
            self.data=json.load(envf)
        
        self.master = master     
        self.hwin = tk.Frame(self.master)
        self.hcomp ={}
        self.hframes={}
        
        self.init_frames()
        self.init_buttons()
        self.hwin.pack()
            
    def init_frames(self):        
        
        i=0
        for key in self.data:
            
            dat1 = self.data[key]
            h = Entryframe(self.hwin,dat1,key)
            if key== 'vstimparam':
                for ename,ih in h.hcomp.items():
                    ih.config(width=50)                
                h.grid(row=i,columnspan=4, sticky=tk.W + tk.E, padx=5, pady=5)
            else:
                h.grid(row=i,columnspan=1, sticky=tk.W, padx=5, pady=5)
            #h.pack( expand=1)
            self.hframes[key]=h
            i +=1
    
    
        
        
    def init_buttons(self):
        nframe = len(self.data)
        h = tk.Button(self.hwin, text='UPDATE', command=self.update_par).grid(row=nframe, column=0, sticky=tk.W, pady=4)
        self.hcomp['update_b']=h
        h = tk.Button(self.hwin, text='SAVE', command=self.save_env).grid(row=nframe, column=2, sticky=tk.W, pady=4)
        self.hcomp['save_b']=h
        h = tk.Button(self.hwin, text='Enable', command=self.entry_enable).grid(row=nframe, column=1, sticky=tk.W, pady=4)
        self.hcomp['save_en']=h

    def update_par(self):
        """
        def update_par(self):
            update data structure from inputs
        """
        for key,hframe in self.hframes.items():                        
            hframe.update_par()
            
            
    def entry_enable(self):
        for key,hframe in self.hframes.items():                        
            hframe.entry_enable()
            
    def entry_disable(self):
        for key,hframe in self.hframes.items():                        
            hframe.entry_disable()
            
    def save_env(self):
        """
        def save_env(self):
            update data structure from inputs
            and save to enviornment file
        """
        self.update_par()
        with open(self.envfile,'wt') as envf:
            j=json.dumps(self.data,indent=4)
            envf.write(j)
        self.entry_disable()   
    
        
class Controlframe:
    def __init__(self,filename):
        self.master = tk.Tk()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.hwin = tk.Frame(self.master)                
        self.fn = filename
        
        self.paramwindow = tk.Toplevel(self.master)
        self.paramframe = Paramframe(self.paramwindow,self.fn)
        self.hcomp ={}
        self.create_uimodules()
        self.hwin.pack()
        self.data =[]
        self.stepper =None
        
    def on_closing(self):
        if self.stepper:
            self.stepper.close()
        self.master.destroy()
        print("Window closed")
    
        
    def create_uimodules(self):

        motor_set={'speed':0,'accel':250}
        h= Entryframe(self.hwin,motor_set,'motor_setting')
        h.grid(row=0,rowspan=2,columnspan=1, sticky=tk.E, padx=5, pady=5)
        self.hcomp['motor_setting']=h
        
        h = tk.Button(self.hwin, text='motor_init', command=self.motor_init).grid(row=0, column=1, sticky=tk.W, pady=4)
        self.hcomp['motor_init']=h
        
        h = tk.Button(self.hwin, text='motor_detach', command=self.motor_detach).grid(row=1, column=1, sticky=tk.W, pady=4)
        self.hcomp['motor_detach']=h
        
        
        h = tk.Button(self.hwin, text='motor_run', command=self.motor_run).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.hcomp['motor_run']=h
        
        h = tk.Button(self.hwin, text='motor_stop', command=self.motor_stop).grid(row=2, column=1, sticky=tk.W, pady=4)
        self.hcomp['motor_stop']=h
        
        
        
        motor_set={'current':'1mA', 'dur':0}
        h= Entryframe(self.hwin,motor_set,'motor_setting')
        h.grid(row=3,columnspan=2, sticky=tk.W, padx=5, pady=5)
        self.hcomp['elec']=h
        
        h = tk.Button(self.hwin, text='elec_stim', command=self.elec_stim).grid(row=4, column=0, sticky=tk.W, pady=4)
        self.hcomp['elec_stim']=h
        
   
    def motor_init(self):   
        if not self.stepper:        
            self.stepper = stepper.Stepperwrapper()
            
    def motor_detach(self):
        if self.stepper:
            self.stepper.close()
            self.stepper = None
            tk.messagebox.showinfo("Info","motor detached")
        
    def motor_run(self):
        if self.stepper:
            self.hcomp['motor_setting'].update_par()
            #tk.messagebox.showinfo("test",str(hf.hcomp['motor_setting'].data['speed']))
            speed = self.hcomp['motor_setting'].hcomp['speed'].get()
            accel = self.hcomp['motor_setting'].hcomp['accel'].get()

            self.stepper.setEngaged(False)             
            self.stepper.setAcceleration(float(accel))
            self.stepper.setVelocityLimit(float(speed))            
            self.stepper.setEngaged(True) 
            self.hcomp['motor_setting'].entry_disable()
        else:
            tk.messagebox.showinfo("Info","motor not initialized")
            
        
        
    def motor_stop(self):
        if self.stepper:
            self.stepper.setEngaged(False)
            self.stepper.setAcceleration(0)
            self.stepper.setVelocityLimit(0)
            self.hcomp['motor_setting'].entry_enable()
    
    def elec_stim(self):
        pass

        
hf = Controlframe('Sang.json')
tk.mainloop( )        