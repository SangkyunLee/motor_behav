# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 15:25:56 2019

@author: slee
"""

from Phidget22.Phidget import *
from Phidget22.Devices.Stepper import *
import math


from time import sleep,time
import json
import random

import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import traceback
import logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

class Timer:
    """ This is a timer that is used for the state system
    time is in milliseconds
    """

    def __init__(self):
        self.start_time = 0
        self.time = time
        self.start()

    def start(self):
        self.start_time = self.time()

    def elapsed_time_ms(self):
        return int((self.time() - self.start_time)*1000)

    def add_delay(self, sec):
        self.start_time += sec
        
def onVelocityChange(self, velocity):  
    elapsed_time = self.timer.elapsed_time_ms()
    print("Velocity: " + str(velocity) +"\tlaptime: " + str(elapsed_time))    
    self.data.append([elapsed_time, velocity])    
    
def onAttach(self):
    self.attached =True
    print("\n===================\nDevice Attach!")

def onDetach(self):
    self.attached =False
    print("\n===================\nDevice Detach!")

    
def onError(self, code, description):
	print("Code: " + ErrorEventCode.getName(code))
	print("Description: " + str(description))
	print("----------")
    
class Stepperwrapper(Stepper):
    def __init__(self, RAD = 8, currentlimit = 1, DataInterval=8,\
                 motor_step_angle = 0.067):
        # default valuse for motor 3327 and wheel radius 8 cm
        super(Stepperwrapper, self).__init__()
        self.motor_step_angle = motor_step_angle
        self.RAD = RAD
        self.currentlimit=currentlimit
        self.DataInterval =DataInterval
        self.angular_scale = None
        self.linear_scale = None
        self.attached = False            
        self.data=[]
        self.timer = []
        
        self.init_device()
            
    def init_device(self):
        self.setOnAttachHandler(onAttach)
        self.setOnDetachHandler(onDetach)
        self.setOnErrorHandler(onError)        
        self.openWaitForAttachment(5000)
        
        self.calculate_scalefactor()
        self.setRescaleFactor(self.linear_scale)
        if self.currentlimit is not None:
            self.setCurrentLimit(self.currentlimit)
        if self.DataInterval is not None:
            self.setDataInterval(self.DataInterval)
        
        # only running mode allowed
        self.setControlMode(StepperControlMode.CONTROL_MODE_RUN)
        # attach velocity event handler
        self.setOnVelocityChangeHandler(onVelocityChange)    
        
        self.timer = Timer()
        
    def calculate_scalefactor(self):        
        self.angular_scale = self.motor_step_angle /16 # degree/sec (angular angle speed)                 
        self.linear_scale = self.angular_scale* self.RAD *math.pi/180 # cm/sec, cm/sec^2
        
    def reset(self):
        self.timer.start()
        self.setVelocityLimit(0.0)
        self.data = []
        

def randomize(seq, nseg_blk):
    """
    def randomize(seq):
        return seq, seqinx after randomizing
    """
    
    n = len(seq)
    
    assert n%nseg_blk ==0, 'seq%nseg_blk should be 0'
    
    ix = list(range(0,n,nseg_blk))
    random.shuffle(ix)
    
    newseq=[]
    ixs=[]
    for i in ix:
        newseq.append(seq[i])
        newseq.append(seq[i+1])
        ixs.append(i)
        ixs.append(i+1)
    return newseq,ixs



class stepper_control:
    def __init__(self,params=None):
        try:
            if params is not None:
                self.stepper = Stepperwrapper(**params)
            else:
                self.stepper = Stepperwrapper()
            
            
        except(KeyError, ValueError) as err:
            logging.error(err,exc_info=True)
        except PhidgetException as ex:    		
            traceback.print_exc()
            print("")
            print("PhidgetException " + str(ex.code) +
                  " (" + ex.description + "): " + ex.details)
            
    def set_accel_speed(self,accel, targetspeed):
        
        minaccel =self.stepper.getMinAcceleration()
        maxaccel = self.stepper.getMaxAcceleration()
        if accel<minaccel:
            accel = minaccel
        if accel>maxaccel:
            accel = maxaccel
        self.stepper.setAcceleration(accel)
        self.stepper.setVelocityLimit(targetspeed)

        
    def start_stepper(self):
#        if not self.stepper.attached:
#            try:
#                self.stepper.init_device()
#            except PhidgetException as ex:
#                traceback.print_exc()
#                print("\n")
#                print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)
#        print(self.__dict__)
                
            
        if not self.stepper.getEngaged():
            self.stepper.setEngaged(True)
        self.reset()
        
    def stop_stepper(self):
        self.stepper.setEngaged(False)

            
    def reset(self):
        self.stepper.reset()
            
    def detach_stepper(self):
        self.stepper.close()
        
            
            
    def rotate_stepper_ramp(self,  speedlist, durlist,accellist, prerotdur=1, postrotdur = 1):
        """
        def rotate_stepper_ramp(self,  speedlist, durlist,accellist, prerotdur=1, postrotdur = 1):
            
            speedlist = [[6,12],[12,24]]; 1st block: ramp from 10 to 20, 2nd block: ramp from 20 to 30 
            durlist = [blocklen, blocklen]            
            accelist = [6, 12] : acceleration cm/sec^2
            When each block duration is longer than the time to reach target speed, 
            after accelation with the given accelation value, the motor rotates at the target speed 
            until the block duration of time pass                                                
            
        """
   		
                      
        sleep(prerotdur)        
        for spd,dur,accel in zip(speedlist,durlist,accellist):
            print(spd,dur,accel)
            spd2 = float(spd[1])
            block_dur = float(dur)        
            
            print('\n\n\n'+str(accel)+'\n\n\n')
            t0 = time() # get current time stamp (second)                
            self.set_accel_speed(accel,spd2)
            block_dur1 = t0+block_dur -time()
            sleep(block_dur1)    
        
        sleep(postrotdur)    
        
    def saveparam(self, fname, inparam):
        """
        def saveparam(self, fname, inparam):
            inparam: inputparam
            
        """
        outparam = inparam
        tmp = self.get_paramset(inparam)
        for (key,value) in tmp.items():
            outparam[key]=value        
        outparam['stepperparam']=self.get_paramset(inparam['stepperparam'])
        
        
        with open(fname,'wt') as envf:    
            j=json.dumps(outparam,indent=4)
            envf.write(j)          
        
        
        
    def get_paramset(self,inparam):
        """
        def get_paramset(self,inparam):
            list all parameters set by parameter inputs
        """        
        return {pn:getattr(self,pn) for pn in inparam if hasattr(self,pn)}
    
    def save_data(self, fname):
        data = np.array(self.stepper.data)
        df = pd.DataFrame({'time(ms)':data[:,0], 'data':data[:,1]})            
        df.to_csv(fname, sep=',', index=False)
        print('Data are saved in '+fname+'.\n')
        
        
    

def main():
    
    envfile ='Stepper_RUN.json'
    with open(envfile) as envf:
        params=json.load(envf)
    
    
    x = datetime.datetime.now()        
    datfname = x.strftime("%y%m%d")+'_'+x.strftime("%X")                
    file_name = './data/'+datfname.replace(':','')+'.csv'
    
    speed_seq = params['speed_seq']    
    speedlist = speed_seq['speedlist']
    accellist = speed_seq['accellist']
    durlist = speed_seq['durlist']
    nseg_blk = speed_seq['nseg_blk']
    prerotdur = speed_seq['prerotdur']
    postrotdur = speed_seq['postrotdur']
    
    if 'randomize' in speed_seq and speed_seq['randomize']:
        speedlist,newinx = randomize(speedlist,nseg_blk)
        durlist = [durlist[i] for i in newinx]
        accellist = [accellist[i] for i in newinx]
        speed_seq['speedlist'] = speedlist # to save parameters
        speed_seq['durlist'] =durlist
        speed_seq['accellist'] = accellist  
   
    try:
        mh = stepper_control(params['stepperparam'])        
        mh.start_stepper()        
        mh.rotate_stepper_ramp(speedlist,durlist, accellist, prerotdur, postrotdur)
    except KeyboardInterrupt:        	
        mh.detach_stepper()
    except PhidgetException as ex:
        traceback.print_exc()
        print("\n")
        print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)
        
    mh.detach_stepper()      
    mh.save_data(file_name)
    try:
        del speed_seq['randomize']
    except KeyError:
        print("Key not found") 
    params['speed_seq']=speed_seq
    parfname = file_name.replace('.csv','.json')
    mh.saveparam(parfname,params)


    #mh.close()


if __name__=='__main__':
    main()
    
        




###################################################
###          generation of Stepper parameters
##########################################################    
#stepperparam={'RAD':8,     # cm
#        'currentlimit':1.7, # Ampere
#        'DataInterval':10,  # millisecond for event handler
#        'motor_step_angle':0.067} # angular degree / step       
#        
#speed_seq={'speedlist': [[0,6], [6,0], [0, 12],[12, 0], [0, 18], [18, 0],[0, 24],[24, 0]],
#           'nseg_blk': 2,
#           'accellist': [12, 12, 12, 12, 12, 12, 12, 12],
#           'durlist': [10, 10, 10, 10, 10, 10, 10, 10],
#           'prerotdur': 20,
#           'postrotdur': 10,
#           'randomize': True}
# 
#        
#params = {'stepperparam': stepperparam, 'speed_seq':speed_seq}        
#        
#import json
#filename='Stepper_RUN.json'
#
#with open(filename,'wt') as envf:    
#    j=json.dumps(params,indent=4)
#    envf.write(j)        
        
        
        
        
        