# -*- coding: utf-8 -*-
import time
import threading
import glob
import os

prevReadedLog = 0
TestFile ='sample2.txt'
def LogFileWriter():
    global prevReadedLog
    with open(TestFile,'r') as f:
        for i,line in enumerate(f):
            if i == prevReadedLog:
                with open('20201206access.log','a') as tf:
                    print(line.strip(),file=tf)
                    print("writed : " + line.strip())
                prevReadedLog += 1
                break

def Worker():
    LogFileWriter()
        
def Scheduler(interval,func):
    BaseTime = time.time()
    NextTime = 0
    print("press Enter to start writting log file")
    input()
    print("start")
    while True:
        t = threading.Thread(target=func)
        t.start()
        t.join()
        NextTime = ((BaseTime-time.time())%interval) or interval
        time.sleep(NextTime)
    
  
try:
    open('20201206access.log','w').close
    FileName = glob.glob('sample*')
    FileName = sorted(FileName)
    
    
    os.system('cls')
    while True:
        for i in range(len(FileName)):
            print(str(i) + " : " + FileName[i])
        print('Select the number of the sample you want to use.')
        buf = input()
        if buf.isdecimal():
            if int(buf) >= 0 and int(buf) <= i:
                TestFile = FileName[int(buf)]
                break
        os.system('cls')
        print("Please input a numerical value.")
    os.system('cls')
    print("Target : " + TestFile)
    Scheduler(1,Worker)
    
except KeyboardInterrupt:
    print("Program ended.")      
