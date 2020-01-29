# -*- coding: utf-8 -*-
"""
Created on Thu Feb 21 13:56:24 2019

This version is different from the original mcc_daq.py
This version incorporate the multi-processes
Therefore, self.data and self.t feed into record functions arguments

@author: slee
"""


from time import sleep

import platform
node = platform.uname()[1]
if node == 'raspberrypi':
    from daqhats import mcc118, OptionFlags,TriggerModes, HatIDs, HatError
    from daqhats_utils import select_hat_device, enum_mask_to_string, \
    chan_list_to_mask
    

from Timer import Timer
from Threadworker import *
import Processworker as pw
import multiprocessing as mp
from Daq import *

import numpy as np
import pdb
import logging

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


READ_ALL_AVAILABLE = -1
DTYPE = 'float32'
class MCC118(DAQ):
    """ mcc118"""

    def __init__(self, params):     
        
        
        #super(DAQ,self).__init__(params)
        super().__init__(params)
        try:                                 
            self.timeout = params['timeout']
            self.acq_dur = params['acq_dur'] # acquistion segment duration
            
        except KeyError:
            raise
            
        if 'timer' in params:
            self.timer = params['timer']            
        else:
            self.timer = Timer()            
            
        self.read_request_size =[] # will be converted from self.acq_dur from init_daq
        self.hat = []  
        if 'save_dir' in params.keys():
            self.fn = get_fn(params['save_dir'])
        else:
            self.fn = None
            
        
        self.init_daq()
              
        #self.worker = Threadworker(self.record)
        #self.worker.setName('DAQthreader_ch'+str(self.ai_ch))
        #self.worker.setName('DAQthreader_ch'+str(self.ai_ch))
        
        #manager = mp.Manager()
        #self.data = manager.list()
        #self.t = manager.list()
        #self.worker = pw.Processworker(target=self.record, args=(self.data,self.t))
        self.worker = pw.Processworker(target=self.record, args=tuple())
        

        
    def init_daq(self):
        try:            
            address = select_hat_device(HatIDs.MCC_118)
            self.hat = mcc118(address)
            
            num_channels = len(self.ai_ch)             
            self.scan_rate = self.hat.a_in_scan_actual_rate(num_channels, self.scan_rate)        
            self.read_request_size = int(self.scan_rate*self.acq_dur)
        
            
            
        except (NameError, SyntaxError):
            pass
        
        
    def reset_timer(self):
        """
        def reset_timer(self):
            reset timer
        """
        self.timer.start()
        
    #def record_cont(self,data,t):
    def record_cont(self):        
        """
        def record_cont(self):
        recording continously while scan_status is running
        """
        
        
        nch  = len(self.ai_ch) 
                
        self.reset_timer()    
        scan_status = self.hat.a_in_scan_status()    
        while self.worker.running() & scan_status.running : 
            
            scan_status = self.hat.a_in_scan_status()
            nsample =scan_status.samples_available
            
            if nsample>= self.read_request_size:                
                read_result = self.hat.a_in_scan_read_numpy(READ_ALL_AVAILABLE, self.timeout)       
                D= read_result.data.astype(DTYPE)         
                elapsed_time = self.timer.elapsed_time()
                self.data_acqtime[self.acq_counter] = elapsed_time 
                logging.debug(scan_status)
                      
                
                nsample = int(len(read_result.data) / nch) # 
                self.data_len[self.acq_counter] =nsample
                
                # Check for an overrun error
                if read_result.hardware_overrun:
                    logging.error('\n\nHardware overrun\n')                
                elif read_result.buffer_overrun:
                    logging.error('\n\nBuffer overrun\n')                
                
                
                if self.fn:
                    dseg = np.reshape(D,(nsample,nch))    
                    timeoff = self.total_nsample_perchannel/self.scan_rate
                    tseg = timeoff + np.array(range(0,nsample), dtype=DTYPE)/self.scan_rate
                    tseg = tseg[:,np.newaxis]
                    data = np.concatenate((tseg,dseg), axis=1)

                    with open(self.fn,'ab') as file:
                        file.write(data)
                        logging.debug('\n===================\n')
                        logging.debug('file name:{}, segment:{} saved'.format(self.fn, self.acq_counter))
                        logging.debug('\n===================\n')
                   
                    
                    
                
                #data.append(np.reshape(D,(nsample,nch)))
                #t.append(timeoff + np.array(range(0,nsample), dtype='float32')/self.scan_rate)                
                
                self.worker.set_datflag()
                
                self.total_nsample_perchannel += nsample
                self.acq_counter +=1
                sleep(self.acq_dur*0.9)
            else:                
                sleep(0.05)
        print("\n===================\nRecording time: " + str(elapsed_time)+"\n")       
                
    def record_N_sample(self):
        """
        def record_N_sample(self):
        read N samples 
        This version of the function is old version.
        TO DO: implement file saving
        
        """
        
        nch  = len(self.ai_ch)                        
        scan_status = self.hat.a_in_scan_status()    
        total_samples_read =0
        segment_size = int(self.scan_rate* 0.1) #set segment size to 100msec
        N = self.read_request_size
        
        if self.worker.running() & scan_status.running :                         
            while total_samples_read <N:                        
                read_result = self.hat.a_in_scan_read_numpy(segment_size, self.timeout)       
                self.data_acqtime[self.acq_counter] = self.timer.elapsed_time()
                nsample = int(len(read_result.data) / nch) #                 
                # Check for an overrun error
                if read_result.hardware_overrun:
                    logging.error('\n\nHardware overrun\n')                
                elif read_result.buffer_overrun:
                    logging.error('\n\nBuffer overrun\n')                
                    
                dataseg = np.reshape(read_result.data,(nsample,nch))
                timeoff = self.total_nsample_perchannel/self.scan_rate
                tseg = timeoff + np.array(range(0,nsample))/self.scan_rate
                t = np.hstack((t,tseg))
                data = np.vstack((data,dataseg))
                self.data_len[self.acq_counter] =nsample
                
                #workername = self.worker.getName()                
                #logging.debug('{}: counter:{}, nsample:{}, abstime:{}'.format(workername,self.acq_counter, nsample, self.data_acqtime[self.acq_counter]))                                                
                
                self.total_nsample_perchannel += nsample
                self.acq_counter +=1
                sleep(segment_size*0.9)
            self.worker.set_datflag() # set data_ready_flag
            
    
    def wait_for_trigger(self):
        """
        Monitor the status of the specified HAT device in a loop until the
        triggered status is True or the running status is False.        
        """
        # Read the status only to determine when the trigger occurs.
        is_running = True
        is_triggered = False
        while is_running and not is_triggered:
            status = self.hat.a_in_scan_status()
            is_running = status.running
            is_triggered = status.triggered
            
            
                
    def record_withtrigger(self):                                
        while self.worker.running():             
            self.wait_for_trigger()
            self.record_N_sample()         
            
                
    def record(self):
        """
        def record(self):
            acqusition start
        """
        
        
        channel_mask = chan_list_to_mask(self.ai_ch)
        
        if self.mode =='continuous':
            samples_per_channel = 0
            options = OptionFlags.CONTINUOUS    
                        
            self.hat.a_in_scan_start(channel_mask, samples_per_channel, self.scan_rate,options)                 
            self.record_cont()
            
            
        elif self.mode=='trigger':
            samples_per_channel = self.read_request_size
            options = OptionFlags.EXTTRIGGER
            trigger_mode = TriggerModes.RISING_EDGE
            
            self.hat.trigger_mode(trigger_mode)
            
            self.hat.a_in_scan_start(channel_mask, samples_per_channel, self.scan_rate,options) 
            self.record_withtrigger()
            
        elif self.mode =='finite':
            samples_per_channel = self.read_request_size
            options = OptionFlags.DEFAULT
            self.hat.a_in_scan_start(channel_mask, samples_per_channel, self.scan_rate,options) 
            self.record_N_sample()
            
            
        else:
            logging.error('not implmented\n')
            raise      
        self.worker.clear_datflag()
    
    def acq_start(self):
        self.worker.start_withflag()
        self.reset_timer()
    
            
    def acq_stop(self):
        self.worker.stop()
        sleep(0.1)
        self.hat.a_in_scan_stop()
        
    def acq_cleanup(self):
        self.hat.a_in_scan_cleanup()
        
        
        
def get_fn(save_dir):        
    import datetime        
    import os
    x = datetime.datetime.now()
    datfname = x.strftime("%X")        
    fn = os.path.join(save_dir,datfname.replace(':','')+'.dat')  
    return fn

def load_data(fn,num_ch):
    """ 
    def load_data(fn,num_ch):
    loading binary data to numpy array
    fn: full filename 
    num_ch: number of channel
    """
    data = np.fromfile(fn,dtype=DTYPE)
    nsample = int(data.size/num_ch)
    data = data.reshape((nsample, num_ch))
    return data        
    
def plot_data(chidx,data):    
    import matplotlib.pyplot as plt
    h= plt.plot(data[:,0],data[:,chidx])
    return h
    
    
    


#import json
#envfile ='Sang.json'
#with open(envfile) as envf:
    #data=json.load(envf)

#daq = MCC118(data['daqparam'])
#daq.acq_start()
#sleep(500)
#daq.acq_stop()

#daq.t[-1][-1]


    
