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
from mcc_daq import *
from mcc_dio import *
#from Ext_trigger import *
from Timer import Timer
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
            h.entry_disable()
            if key== 'vstimparam':
                for ename,ih in h.hcomp.items():
                    ih.config(width=50)                
                h.grid(row=i,columnspan=2, sticky=tk.W, padx=5, pady=5)
            else:
                h.grid(row=i,column=0, sticky=tk.W, padx=5, pady=5)
            #h.pack( expand=1)
            self.hframes[key]=h
            i +=1
    
    
        
        
    def init_buttons(self):
        
        pass
        #nframe = len(self.data)
        #h = tk.Button(self.hwin, text='UPDATE', command=self.update_par).grid(row=nframe, column=0, sticky=tk.W, pady=4)
        #self.hcomp['update_b']=h
        #h = tk.Button(self.hwin, text='SAVE', command=self.save_env).grid(row=nframe, column=2, sticky=tk.W, pady=4)
        #self.hcomp['save_b']=h
        #h = tk.Button(self.hwin, text='Enable', command=self.entry_enable).grid(row=nframe, column=1, sticky=tk.W, pady=4)
        #self.hcomp['save_en']=h

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
        
        self.stepper =None
        self.dio = None       
        self.daq = None        
        
        self.motor_time =[]  # motor start and stop time      
        self.motor_speed=[]  # motor speed
        self.elec_time=[]   # record for elecstim onset time and duration
        
        self.timer = Timer() # set timer
        self.motor_timer = None
        
    def on_closing(self):
        if self.stepper:
            self.stepper.close()
        if self.daq:
            self.daqstop()    
        self.master.destroy()        
        
        print("Window closed")
    
    def save_trialdata(self):
        """
        def save_trialdata(self):
        save trial data for motor rotation time (start, end) and motor speed
        and elecstim (start, duration)
        """
        
        output_tr ={'motor_time':self.motor_time, 'motor_speed': self.motor_speed,
            'elec_time':self.elec_time}
        outpar = self.paramframe.data
        outpar.update({'trial_data':output_tr})
        if outpar['daqparam']['timer']:
            outpar['daqparam']['timer']=[]
        if self.daq and self.daq.fn:
            fn = self.daq.fn
            idx = fn.find('.dat')
            outpar_fn = fn[:idx]+'.json'            
        else:
            import datetime            
            x = datetime.datetime.now()
            datfname = x.strftime("%X")        
            daqparam = self.paramframe.data['daqparam']
            if daqparam['save_dir']:
                save_dir = daqparam['save_dir']
            else:
                save_dir ='.'
            outpar_fn = path.join(save_dir,datfname.replace(':','')+'.json')
            
        with open(outpar_fn,'wt') as envf:
            j=json.dumps(outpar, indent=4)
            envf.write(j)
            tk.messagebox.showinfo("SAVE","Trialdata_saved in:{}".format(outpar_fn))
            
        
    def create_uimodules(self):

        h = tk.Button(self.hwin, text='DAQ start', command=self.daqstart)
        h.grid(row=0, column=0, pady=4)
        self.hcomp['daqstart_b']=h
        
        h = tk.Button(self.hwin, text='DAQ stop', command=self.daqstop)
        h.grid(row=0, column=1, pady=4)
        self.hcomp['daqstop_b']=h
        
        h = tk.Button(self.hwin, text='motor_init', command=self.motor_init)
        h.grid(row=1, column=0,  pady=4)
        self.hcomp['motor_init']=h
        
        h = tk.Button(self.hwin, text='motor_det', command=self.motor_detach)
        h.grid(row=1, column=1,pady=4)
        self.hcomp['motor_detach']=h
        
        
        motor_set={'speed':50,'accel':250, 'dur':30}
        h= Entryframe(self.hwin,motor_set,'motor_setting')
        h.grid(row=2,rowspan=3,column=0, columnspan=2, padx=5, pady=5)
        self.hcomp['motor_setting']=h
        
        
        
        
        h = tk.Button(self.hwin, text='motor_run', command=self.motor_run)
        h.grid(row=5, column=0,  pady=4)
        self.hcomp['motor_run']=h
        
        h = tk.Button(self.hwin, text='motor_stop', command=self.motor_stop)
        h.grid(row=5, column=1, pady=4)
        self.hcomp['motor_stop']=h
        
        
        
        DIO_set={'Ch.':6, 'dur':0,'delay':0, 'motor_delay':0}
        h= Entryframe(self.hwin,DIO_set,'DIO_setting')
        h.grid(row=6,columnspan=2, padx=2, pady=5)
        self.hcomp['elec']=h
        
        h = tk.Button(self.hwin, text='DIO_init', command=self.DIO_init)
        h.grid(row=7, column=0, pady=4)
        self.hcomp['DIO_init']=h
        
        h = tk.Button(self.hwin, text='elec_stim', command=self.DIO_output)
        h.grid(row=7, column=1, pady=4)
        self.hcomp['elec_stim']=h
        
        h = tk.Button(self.hwin, text='save_trialdata', command=self.save_trialdata)
        h.grid(row=8, column=0, pady=4)
        self.hcomp['save_trialdata']=h
        
        
    def daqstart(self):
        if self.daq:
            self.daq = None         
        daqparam = self.paramframe.data['daqparam']
        daqparam['timer']=self.timer
        self.daq = MCC118(daqparam)        
        self.daq.acq_start()
        tk.messagebox.showinfo("DAQ-Info","DAQ_started. filename:{}".format(self.daq.fn))
        h= self.hcomp['daqstart_b']        
        h['state'] = tk.DISABLED
        
        
    def daqstop(self):  
        if self.daq:      
            self.daq.acq_stop()     
        
        h=self.hcomp['daqstart_b']
        h['state'] = tk.NORMAL

        
   
    def motor_init(self):   
        if not self.stepper:        
            self.stepper = stepper.Stepperwrapper()
            h= self.hcomp['motor_init']        
            h['state'] = tk.DISABLED
            
    def motor_detach(self):
        if self.stepper:
            self.stepper.close()
            self.stepper = None
            tk.messagebox.showinfo("Info","motor detached")
            h= self.hcomp['motor_init']
            h['state'] = tk.NORMAL
        
    def motor_run(self):
        if self.stepper:
            self.hcomp['motor_setting'].update_par()
            #tk.messagebox.showinfo("test",str(hf.hcomp['motor_setting'].data['speed']))
            speed = self.hcomp['motor_setting'].hcomp['speed'].get()
            accel = self.hcomp['motor_setting'].hcomp['accel'].get()
            dur = self.hcomp['motor_setting'].hcomp['dur'].get()
            dur = float(dur)

            self.stepper.setEngaged(False)             
            self.stepper.setAcceleration(float(accel))
            self.stepper.setVelocityLimit(float(speed))    
            # record trial info
            motor_start_time=self.timer.elapsed_time()            
            self.motor_time.append(motor_start_time) 
            self.motor_speed.append(float(speed))       
            self.stepper.setEngaged(True)             
            self.hcomp['motor_setting'].entry_disable()
            if dur>0:                
                self.motor_timer =Threadworker(self.motor_stop_timer)
                self.motor_timer.start()
        else:
            tk.messagebox.showinfo("Info","motor not initialized")
            
    def motor_stop_timer(self):
        self.hcomp['motor_setting'].update_par()
        dur = self.hcomp['motor_setting'].hcomp['dur'].get()
        dur = float(dur)
        if dur>0:
            t0= self.timer.elapsed_time()
            t=t0
            while  self.motor_timer.running() and (t-t0)<dur*1000: #timer is millisecond 
                sleep(0.05)
                
                t=self.timer.elapsed_time()
                logging.debug('et:{}'.format(t-t0))
            if (t-t0)>dur*1000: # when entire duration pass, stop    
                self.motor_stop()
            
            
        
    def motor_stop(self):
        if self.stepper:
            self.motor_time.append(self.timer.elapsed_time())
            self.stepper.setVelocityLimit(0)
            #self.stepper.setAcceleration(0)
            self.stepper.setEngaged(False)                        
            self.hcomp['motor_setting'].entry_enable()
        if self.motor_timer and self.motor_timer.running():
            self.motor_timer.stop()  
            
            
            
            
            
                
    
    
    #def save_daq(self, fn=None):
        #import pandas as pd
        #if fn:
            #file_name = './motor_data/'+fn
        #else:            
            #import datetime        
            #x = datetime.datetime.now()
            #datfname = x.strftime("%X")        
            #file_name = '../motor_data/'+datfname.replace(':','')+'.csv'            
        #data = np.concatenate(self.daq.data, axis =0)
        #t = np.concatenate(self.daq.t, axis =0)


        #daqparam = hf.paramframe.data['daqparam']
        #out ={}
        #for i,ch in enumerate(daqparam['ai_ch']):
        #    out['CH'+ str(ch)]=data[:,i] 


        #df = pd.DataFrame(out, index = t)       
        #df.index.name ='Time(sec)'     
        #df.to_csv(file_name, sep=',')        
        
   
    

        
    
    def DIO_init(self):
        if not self.dio:
            dioparam = self.paramframe.data['dioparam']
            self.dio = MCC152_DIO(dioparam)
        else:
            self.dio.init_dev()        
        
            
            
    
    def DIO_output(self):
        channels = self.paramframe.data['dioparam']['do_ch'] 
        ch = self.hcomp['elec'].hcomp['Ch.'].get()
        ch = int(ch)
        #print(type(ch))
        #ch = int(ch)
        #tk.messagebox.showinfo("Info",type(ch))
        dur_sec = float(self.hcomp['elec'].hcomp['dur'].get())
        delay = float(self.hcomp['elec'].hcomp['delay'].get())
        motor_delay = float(self.hcomp['elec'].hcomp['motor_delay'].get())
        if ch in channels  and self.dio:        
            sleep(delay)  
            self.elec_time.append(self.timer.elapsed_time())   
            self.elec_time.append(dur_sec)   
            for i in range(5):
                self.dio.write_outputvalue(ch, 1)                            
                sleep(dur_sec)
                self.dio.write_outputvalue(ch, 0)
        
            
        else:
            msg = "ch"+str(ch)+" not opened or device not attached"
            tk.messagebox.showinfo("Info",msg)
        # motor_delay<0, motor behavior is independent of elec stim
        # motor_delay==0, motor stops immediately
        # motor_delay>0, motor stops 'motor_delay' after elec stim        
        if motor_delay>=0:
            sleep(motor_delay)
            self.motor_stop()
            
            
def main():
        
    hf = Controlframe('Sang.json')
    tk.mainloop( )   



if __name__=='__main__':
    main()     

#ch=6
#dur1=0.01
#dur2=1
#try:	
    #while True:
        #hf.dio.write_outputvalue(ch, 1)
        #sleep(dur1)
        #hf.dio.write_outputvalue(ch, 0)
        #sleep(dur1)
        #hf.dio.write_outputvalue(ch, 1)
        #sleep(dur1)
        #hf.dio.write_outputvalue(ch, 0)
        #sleep(dur1)
        #hf.dio.write_outputvalue(ch, 1)
        #sleep(dur1)
        #hf.dio.write_outputvalue(ch, 0)
        #sleep(dur2)
#except KeyboardInterrupt:
    #print("Interrupted")

        
#fn = '../motor_data/152804.csv'
#pdat = pd.read_csv(fn)
# spd:66, accel:250 works but not very long
