# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 09:40:24 2019

@author: slee
"""


import multiprocessing as mp
from multiprocessing import Manager

class Processworker(mp.Process):
    """ Threadworker"""

    def __init__(self, target, args):     
        
        super().__init__(target=target, args=args)
        
        self.runflag = mp.Event()  # clear this to pause thread
        self.runflag.clear()
        self.dataflag = mp.Event() 
        self.dataflag.clear()
        

    def set_datflag(self):
        self.dataflag.set()
    def clear_datflag(self):
        self.dataflag.clear()
    
    def check_datflag(self):
        return self.dataflag.is_set()


    def start_withflag(self):
        self.dataflag.clear()
        self.runflag.set()
        self.start()

    def stop(self):
        self.runflag.clear()
        self.dataflag.clear()

    def resume(self):
        self.runflag.set()

    def running(self):
        return (self.is_alive() and self.runflag.is_set())

    def kill(self):
        self.kill()
        print("WORKER END")
        
        

   

    



    
 


